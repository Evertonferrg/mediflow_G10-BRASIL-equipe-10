
# teste_etapa5.py
# Objetivo: rodar o grafo e arquivar o resultado nas pastas certas.

import os
from app.schemas import Extracao, Paciente, Medico
from app.grafo import triar
from app.resposta import arquivar

def extrator_falso(extracao):
    return lambda texto: extracao

def processar(documento_id, texto, extrator):
    estado = triar(texto, extrator)                  # roda o grafo
    resposta = arquivar(documento_id, texto, estado) # salva em buckets
    print(f"{documento_id} -> {resposta['decisao_roteamento']['destino_principal']}"
          f" | salvo em: {resposta['armazenamento_oci']['caminho_objeto']}")

processar("DOC-ROTINA-001",
    "RECEITA. Paciente: Maria Souza, 34 anos. Solicitante: Dr. Paulo Lima CRM-SP 123456.",
    extrator_falso(Extracao(
        tipo_documento="Receituário Médico", nivel_prioridade="Rotina",
        score_confianca_classificacao=0.9,
        paciente=Paciente(nome="Maria Souza", idade=34),
        medico_solicitante=Medico(nome="Dr. Paulo Lima", crm="CRM-SP 123456"))))

processar("DOC-URGENTE-002",
    "LAUDO. Paciente: Carlos Eduardo Mendes, 52 anos. Solicitante: Dra. Renata Silveira CRM-SP 145892. TEP agudo.",
    extrator_falso(Extracao(
        tipo_documento="Laudo de Exame de Imagem", nivel_prioridade="Urgente",
        score_confianca_classificacao=1.0,
        paciente=Paciente(nome="Carlos Eduardo Mendes", idade=52),
        medico_solicitante=Medico(nome="Dra. Renata Silveira", crm="CRM-SP 145892"),
        diagnostico_principal="Tromboembolismo Pulmonar Agudo")))

processar("DOC-AMBIGUO-003",
    "Receita manuscrita. Medicamento ilegível 10mg.",
    extrator_falso(Extracao(
        tipo_documento="Receituário Médico", nivel_prioridade="Rotina",
        score_confianca_classificacao=0.55,
        inconsistencias=["medicamento ilegível"])))

# Mostra todos os arquivos que foram criados
print("\nArquivos criados:")
for pasta, _, arquivos in os.walk("storage_local"):
    for a in arquivos:
        print(" ", os.path.join(pasta, a))