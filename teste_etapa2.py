# teste_etapa2.py
# Objetivo: ver o Gemini transformar um laudo em dados estruturados.

from app.llm import extrair

#Laudo de exemplo tirado do PDF do hackthon
laudo = (
    "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO."
    "Paciente: Carlos Eduardo Mendes, 52 anos, "
    "Solicitante: Dra. Renata Silveira CRM-SP 145892. "
    "Exame: Tomografia de Torax com contraste. "
    "Indicacao: Suspeita de embolia pumonar aguda, dispneia subita. "
    "CONCLUSÃO: Quadro compativel com Tromboembolismo Pulmonar Agudo. "
    "Sugere-se correlacao clinica urgente."
)

resultado = extrair(laudo)

#model_dump_json(ident=2) imprime o json bonito e legivel
print(resultado.model_dump_json(indent=2))