
# app/resposta.py
# Objetivo: transformar o estado final do grafo no JSON de resposta do projeto
# e salvar documento + decisão nos "buckets" certos.

from . import storage

# Em qual pasta cada destino é arquivado
PASTAS = {
    "Fila_Emergencia_Medica": "processados/urgentes",
    "Fila_Revisao_Humana": "auditoria_humana",
}
PASTA_ROTINA = "processados/rotina"

def montar_resposta(documento_id: str, estado: dict) -> dict:
    e = estado.get("extracao")     # objeto Extracao, ou None se o LLM falhou
    return {
        "status": "processado" if e else "erro_extracao",
        "documento_id": documento_id,
        "classificacao": ({
            "tipo_documento": e.tipo_documento,
            "nivel_prioridade": e.nivel_prioridade,
            "score_confianca": estado["score"],   # nosso score, não o do LLM
        } if e else None),
        "dados_extraidos": e.model_dump() if e else None,
        "problemas": estado.get("problemas", []),
        "decisao_roteamento": {
            "destino_principal": estado["destino"],
            "requer_auditoria_humana": estado["requer_revisao"],
            "justificativa_roteamento": estado["justificativa"],
            "notificacao_gerada": estado.get("notificacao"),
        },
    }

def arquivar(documento_id: str, texto: str, estado: dict) -> dict:
    """Salva o texto original em recebidos/ e a decisão na pasta do destino."""
    resposta = montar_resposta(documento_id, estado)
    pasta = PASTAS.get(estado["destino"], PASTA_ROTINA)

    storage.salvar(f"recebidos/{documento_id}.txt", texto)
    resposta["armazenamento_oci"] = storage.salvar(
        f"{pasta}/{documento_id}.json", resposta)
    return resposta
