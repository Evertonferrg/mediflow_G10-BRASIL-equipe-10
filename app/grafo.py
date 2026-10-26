
# app/grafo.py
# Objetivo: conectar extração + validação + roteamento em um grafo de decisão.

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from .llm import extrair
from .validacao import validar, precisa_revisao

# ---------- ESTADO ----------
# Dicionário compartilhado entre os nós. total=False: nem todo campo existe desde o início.
class Estado(TypedDict, total=False):
    texto: str                 # texto original do documento (entrada)
    extracao: Optional[object] # objeto Extracao (ou None se o LLM falhou)
    erro: Optional[str]        # mensagem de erro, se algo falhou
    problemas: list            # problemas achados pela validação
    score: float               # score final calculado por nós
    destino: str               # para onde o documento vai
    requer_revisao: bool       # precisa de humano?
    justificativa: str         # por que esse destino
    notificacao: Optional[dict]  # alerta gerado (se houver)

# Destinos de rotina por tipo de documento
DESTINOS_ROTINA = {
    "Receituário Médico": "Farmacia_Hospitalar",
    "Guia de Solicitação de Procedimento": "Auditoria_Autorizacoes",
}
PADRAO = "Prontuario_Eletronico"

def construir_grafo(extrator=extrair):
    """Monta e devolve o grafo. O parâmetro 'extrator' permite trocar o LLM
    por uma versão falsa nos testes (sem gastar cota nem depender de rede)."""

    # ---------- NÓS ----------
    def n_extrair(s: Estado):
        try:
            return {"extracao": extrator(s["texto"])}
        except Exception as e:            # qualquer falha do LLM vira "erro", não quebra
            return {"extracao": None, "erro": str(e)}

    def n_validar(s: Estado):
        if s.get("erro"):                 # sem extração, não há o que validar
            return {"problemas": [], "score": 0.0}
        extracao, problemas, score = validar(s["extracao"], s["texto"])
        return {"extracao": extracao, "problemas": problemas, "score": score}

    def n_urgencia(s: Estado):
        e = s["extracao"]
        achado = e.diagnostico_principal or e.tipo_documento
        return {
            "destino": "Fila_Emergencia_Medica",
            "requer_revisao": False,
            "justificativa": f"Achado crítico detectado: {achado}.",
            "notificacao": {"canal": "Alerta_Plantao_Medico",
                            "mensagem": f"ALERTA URGENTE: {achado} - paciente {e.paciente.nome}."},
        }

    def n_revisao(s: Estado):
        if s.get("erro"):
            motivo = f"Falha na extração automática: {s['erro'][:80]}"
            notificacao = None
        else:
            motivo = "; ".join(s["problemas"]) or f"Score baixo ({s['score']})"
            # Se parecia urgente mas está duvidoso, avisa mesmo assim:
            # urgência incerta não pode ficar esperando na fila.
            urgente = s["extracao"].nivel_prioridade == "Urgente"
            notificacao = ({"canal": "Alerta_Plantao_Medico",
                            "mensagem": "Possível urgência com dados ambíguos: revisar com prioridade."}
                           if urgente else None)
        return {"destino": "Fila_Revisao_Humana", "requer_revisao": True,
                "justificativa": motivo, "notificacao": notificacao}

    def n_padrao(s: Estado):
        destino = DESTINOS_ROTINA.get(s["extracao"].tipo_documento, PADRAO)
        return {"destino": destino, "requer_revisao": False,
                "justificativa": f"Documento de rotina encaminhado para {destino}.",
                "notificacao": None}

    # ---------- ARESTA CONDICIONAL ----------
    # Lê o estado e devolve o NOME do próximo nó. A ordem das regras importa:
    # primeiro a segurança (revisão), depois urgência, por fim a rotina.
    def decidir(s: Estado) -> str:
        if s.get("erro") or precisa_revisao(s["score"], s["problemas"]):
            return "revisao"
        if s["extracao"].nivel_prioridade == "Urgente":
            return "urgencia"
        return "padrao"

    # ---------- MONTAGEM ----------
    g = StateGraph(Estado)
    g.add_node("extrair", n_extrair)
    g.add_node("validar", n_validar)
    g.add_node("urgencia", n_urgencia)
    g.add_node("revisao", n_revisao)
    g.add_node("padrao", n_padrao)

    g.set_entry_point("extrair")           # onde o fluxo começa
    g.add_edge("extrair", "validar")       # aresta fixa
    g.add_conditional_edges("validar", decidir,   # aresta condicional
                            {"urgencia": "urgencia", "revisao": "revisao", "padrao": "padrao"})
    for no in ("urgencia", "revisao", "padrao"):
        g.add_edge(no, END)                # os três terminam o fluxo

    return g.compile()

def triar(texto: str, extrator=extrair) -> dict:
    """Função de conveniência: roda o grafo e devolve o estado final."""
    return construir_grafo(extrator).invoke({"texto": texto})