"""Montagem das dependencias a partir da configurançâo. """
from __future__ import annotations

from app.agente.grafo import criar_agente
from app.config import Config
from app.servicos.armazenamento import criar_armazenamneto
from app.servicos.llm import criar_extrator
from app.servicos.notificacao import Notificador
from app.servicos.triagem import TriagemServico

def montar_servico(config: Cponfig | None = None) -> TriagemServico:
    config = config or Config.carregar()
    agente = criar_agente(
        criar_extrator(config), Notificador(config.slack_webhook_url), config.confianca_minima
        
    )
    return TriagemServico(agente, criar_armazenamneto(config))
