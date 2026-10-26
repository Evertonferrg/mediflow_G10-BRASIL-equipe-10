from app.schemas import Extracao
# ---------- TESTE 1: dados válidos ----------
# Criamos uma Extracao informando só os campos obrigatórios.
# Os demais (paciente, medicamentos etc.) recebem os valores padrão.

ok = Extracao(
    tipo_documento="Receituário Médico",
    nivel_prioridade="Rotina",
    score_confianca_classificacao=0.9, #0.9 esta entre 0 e 1, então passa
)

#Model_dump() converte o objeto em dicionario python (vira Json depois)
print("TESTE 1 (válido):")
print(ok.model_dump())

# ---------- TESTE 2: dados inválidos ----------
# O score 1.7 viola a regra Field(ge=0, le=1) do schema.
# Usamos try/except para capturar o erro e continuar o programa.

print("\nTESTE 2 (inválido):")
try:
    Extracao(
        tipo_documento="X",
        nivel_prioridade="Rotina",
        score_confianca_classificacao=1.7, # Fora do limite
    )

except Exception as erro:
    #O pydantic levanta validationError explicando qual campo falhou
    print("Pydantic rejeitou: ", erro)