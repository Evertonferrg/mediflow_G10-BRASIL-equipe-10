# teste_etapa4.py
#Objetivo: ver o grafo escolhendo o caminho certo em 4 situações.
# Usa um "extrator falso" (sem Gemini), então roda offline e de graça.

from app.schemas import Extracao, Paciente, Medico
from app.grafo import triar

def extrator_falso(extracao):
    """Cria uma função que ignora o texto e devolve sempre a extração dada."""
    return lambda texto: extracao

def extrator_que_falha(texto):
    raise RuntimeError("503 UNAVAILABLE (simulado)")

def mostrar(titulo, texto, extrator):
    r = triar(texto, extrator)
    print(f"\n=== {titulo} ===")
    print("Destino        :", r["destino"])
    print("Requer revisão :", r["requer_revisao"])
    print("Justificativa  :", r["justificativa"])
    print("Notificação    :", r["notificacao"])

# CASO 1: rotina (receita completa)
mostrar("Caso 1: rotina",
        "RECEITA. Paciente: Maria Souza, 34 anos. Solicitante: Dr. Paulo Lima CRM-SP 123456.",
        extrator_falso(Extracao(
            tipo_documento="Receituário Médico", nivel_prioridade="Rotina",
            score_confianca_classificacao=0.9,
            paciente=Paciente(nome="Maria Souza", idade=34),
            medico_solicitante=Medico(nome="Dr. Paulo Lima", crm="CRM-SP 123456"))))

# CASO 2: urgência (laudo de TEP)
mostrar("Caso 2: urgência",
        "LAUDO. Paciente: Carlos Eduardo Mendes, 52 anos. Solicitante: Dra. Renata Silveira CRM-SP 145892. TEP agudo.",
        extrator_falso(Extracao(
            tipo_documento="Laudo de Exame de Imagem", nivel_prioridade="Urgente",
            score_confianca_classificacao=1.0,
            paciente=Paciente(nome="Carlos Eduardo Mendes", idade=52),
            medico_solicitante=Medico(nome="Dra. Renata Silveira", crm="CRM-SP 145892"),
            diagnostico_principal="Tromboembolismo Pulmonar Agudo")))

# CASO 3: ambíguo (faltam dados e há trecho ilegível)
mostrar("Caso 3: ambíguo",
        "Receita manuscrita. Medicamento ilegível 10mg.",
        extrator_falso(Extracao(
            tipo_documento="Receituário Médico", nivel_prioridade="Rotina",
            score_confianca_classificacao=0.55,
            inconsistencias=["medicamento ilegível"])))

# CASO 4: o LLM falha (como o 503 que você viu)
mostrar("Caso 4: LLM fora do ar", "qualquer texto", extrator_que_falha)