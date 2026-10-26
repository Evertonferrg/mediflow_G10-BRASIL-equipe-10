# teste_etapa3.py
# Objetivo: ver a validação reagindo a 3 situações controladas.
# Não chama o Gemini: montamos as extrações à mão, sem gastar cota nem depender de rede.

from app.schemas import Extracao, Paciente, Medico
from app.validacao import validar, precisa_revisao

# Texto "original" do documento, contra o qual a validação confere os nomes
TEXTO = ("LAUDO. Paciente: Carlos Eduardo Mendes, 52 anos. "
         "Solicitante: Dra. Renata Silveira CRM-SP 145892. TEP agudo.")

def mostrar(titulo, extracao):
    # validar devolve 3 coisas: extração corrigida, lista de problemas e score final
    ext, problemas, score = validar(extracao, TEXTO)
    print(f"\n=== {titulo} ===")
    print("CRM normalizado :", ext.medico_solicitante.crm)
    print("Score final     :", score)
    print("Problemas       :", problemas or "nenhum")
    print("Vai p/ revisão? :", precisa_revisao(score, problemas))

# CASO 1: extração boa (CRM "sujo", como o Gemini devolveu; o LLM se acha perfeito)
mostrar("Caso 1: extração boa", Extracao(
    tipo_documento="Laudo de Exame de Imagem",
    nivel_prioridade="Urgente",
    score_confianca_classificacao=1.0,
    paciente=Paciente(nome="Carlos Eduardo Mendes", idade=52),
    medico_solicitante=Medico(nome="Dra. Renata Silveira", crm="CRM-SP 145892"),
))

# CASO 2: faltam dados críticos (sem paciente e sem CRM)
mostrar("Caso 2: sem CRM e sem paciente", Extracao(
    tipo_documento="Receituário Médico",
    nivel_prioridade="Rotina",
    score_confianca_classificacao=0.9,
))

# CASO 3: o LLM "inventou" um nome que não está no texto original
mostrar("Caso 3: nome inventado", Extracao(
    tipo_documento="Laudo de Exame de Imagem",
    nivel_prioridade="Rotina",
    score_confianca_classificacao=0.95,
    paciente=Paciente(nome="Roberto Alves Lima", idade=40),
    medico_solicitante=Medico(nome="Dra. Renata Silveira", crm="145892-SP"),
))