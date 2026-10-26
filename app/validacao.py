# app/validacao.py
# Objetivo: desconfiar do LLM. Normaliza dados, procura problemas
# e calcula um score de confiança próprio.

import re
import unicodedata
from .schemas import Extracao

# Abaixo deste score, o documento vai para revisão humana
LIMIAR_CONFIANCA = 0.75

# Só estas siglas são aceitas como UF do CRM.
UFS_VALIDAS = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
               "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}

# Quanto cada problema desconta do score (valores ajustáveis)
PENALIDADES = {
    "paciente_ausente": 0.30,
    "crm_ausente": 0.25,
    "tipo_desconhecido": 0.40,
    "inconsistencia": 0.20,        # por cada item na lista de inconsistências
    "nome_nao_encontrado": 0.30,   # nome extraído não aparece no texto original
}

def _simplificar(texto: str) -> str:
    """Remove acentos e passa para minúsculas, para comparar textos."""
    texto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return sem_acento.lower()

def normalizar_crm(crm):
    """Converte 'CRM-SP 145892' (ou variações) para '145892-SP'.
    Devolve None se não achar número e UF VÁLIDA."""
    if not crm:
        return None
    numero = re.search(r"\d{3,7}", crm)

    # Procura TODAS as siglas de 2 letras (e não só a primeira),
    # depois de remover a palavra CRM
    candidatas = re.findall(r"\b([A-Za-z]{2})\b", crm.upper().replace("CRM", ""))

    # Fica só com as que são estados de verdade
    ufs = [c for c in candidatas if c in UFS_VALIDAS]

    # Precisa do número E de uma UF válida
    if numero and ufs:
        return f"{numero.group()}-{ufs[0]}"
    return None

def _nome_aparece_no_texto(nome: str, texto: str) -> bool:
    """Confere se TODAS as palavras do nome estão no texto original.
    Ignora títulos como Dr./Dra. Protege contra nomes inventados."""
    texto_s = _simplificar(texto)
    palavras = [p for p in re.findall(r"\w+", _simplificar(nome))
                if p not in ("dr", "dra")]
    return all(p in texto_s for p in palavras)

def validar(extracao: Extracao, texto_original: str):
    """Recebe a extração do LLM e o texto original.
    Devolve: (extracao_corrigida, lista_de_problemas, score_final)."""
    problemas = []
    penalidade = 0.0

    # 1) Normalização: padroniza o CRM
    extracao.medico_solicitante.crm = normalizar_crm(extracao.medico_solicitante.crm)

    # 2) Campos críticos ausentes
    if not extracao.paciente.nome:
        problemas.append("Nome do paciente ausente")
        penalidade += PENALIDADES["paciente_ausente"]
    if not extracao.medico_solicitante.crm:
        problemas.append("CRM do solicitante ausente ou inválido")
        penalidade += PENALIDADES["crm_ausente"]
    if extracao.tipo_documento == "Desconhecido":
        problemas.append("Tipo de documento não identificado")
        penalidade += PENALIDADES["tipo_desconhecido"]

    # 3) Inconsistências que o próprio LLM apontou
    for item in extracao.inconsistencias:
        problemas.append(f"Inconsistência: {item}")
        penalidade += PENALIDADES["inconsistencia"]

    # 4) O nome extraído realmente existe no texto? (anti-alucinação)
    nome = extracao.paciente.nome
    if nome and not _nome_aparece_no_texto(nome, texto_original):
        problemas.append(f"Nome '{nome}' não encontrado no texto original")
        penalidade += PENALIDADES["nome_nao_encontrado"]

    # 5) Score final: parte do score do LLM, limitado a 0.95
    #    (nunca confiamos 100% em autoavaliação), menos as penalidades.
    base = min(extracao.score_confianca_classificacao, 0.95)
    score_final = max(0.0, round(base - penalidade, 2))

    return extracao, problemas, score_final

def precisa_revisao(score: float, problemas: list) -> bool:
    """Regra simples: score baixo OU qualquer problema encontrado."""
    return score < LIMIAR_CONFIANCA or len(problemas) > 0