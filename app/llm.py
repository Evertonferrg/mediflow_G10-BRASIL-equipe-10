#app/llm.py
# Objetivo: enviar o texto de um documento ao Gemini e receber um objetivo Extracao.

import os
from dotenv import load_dotenv
from google import genai
from .schemas import Extracao

load_dotenv()

#Instrucões para o modelo. Em saúde, a regra mais importante e NÂO INVENTAR.
PROMPT = """Você é um auditor clinico. Analise o documento abaixo.

Regras:
    - Nunca invente dados. Se uma informação não estiver no texto, use null.
    - tipo_documento: escolha entre "Receituario Médico", "Laudo de Exame de Imagem", 
    "Laudo Laboratorial", "Guia de Solicitação de Procedimento",
    "Relatorio de Alta", "Atestado Médico" ou "Desconhecido".
    - nivel_prioridade: "Urgente" para achados criticos (ex.: embolia pummonar, infarto, AVC, sepse); caso contrário "Rotina".
    - score_confianca_classificacao: de 0 a 1. Diminua se o texto for ambiguo ou ilegivel.
    - Liste em 'inconsistencias' qualquer trecho ilegível ou contraditório.

DOCUMENTO:
{texto}"""

def extrair(texto: str) -> Extracao:
    #cria o cliente usando a chave guardada no .env
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # chama o modelo. As duas linhas do 'config' são o que força JSON no
    # formato do nosso schema (response_schema=Extracao).
    resposta = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=PROMPT.format(texto=texto),
        config={
            "response_mime_type": "application/json",
            "response_schema": Extracao,
            "temperature": 0, #0 respostas mais estáveis e menos "criativas"
        },
    )

    #Resposta.text é uma string Json: o Pydantic converte E valida de uma vez
    return Extracao.model_validate_json(resposta.text)