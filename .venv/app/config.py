"""Configuração central, lida de variáveis de ambiente (.env opcional)."""
from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv é opcional em produção
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


@dataclass(frozen=True)
class Config:
    armazenamento: str = "memoria"
    bucket: str = "mediflow-documentos-clinicos"
    oci_auth: str = "config"
    oci_config_arquivo: str = "~/.oci/config"
    oci_perfil: str = "DEFAULT"
    oci_namespace: str | None = None
    oci_compartment_id: str | None = None
    llm_provedor: str = "heuristico"
    gemini_api_key: str | None = None
    gemini_modelo: str = "gemini-2.5-flash"
    anthropic_api_key: str | None = None
    anthropic_modelo: str = "claude-sonnet-5-5"
    confianca_minima: float = 0.75
    slack_webhook_url: str | None = None

    @classmethod
    def carregar(cls) -> "Config":
        env = os.environ.get
        return cls(
            armazenamento=env("ARMAZENAMENTO", "memoria").strip().lower(),
            bucket=env("OCI_BUCKET", "mediflow-documentos-clinicos"),
            oci_auth=env("OCI_AUTH", "config").strip().lower(),
            oci_config_arquivo=env("OCI_CONFIG_ARQUIVO", "~/.oci/config"),
            oci_perfil=env("OCI_PERFIL", "DEFAULT"),
            oci_namespace=env("OCI_NAMESPACE") or None,
            oci_compartment_id=env("OCI_COMPARTMENT_ID") or None,
            llm_provedor=env("LLM_PROVEDOR", "heuristico").strip().lower(),
            gemini_api_key=env("GEMINI_API_KEY") or None,
            gemini_modelo=env("GEMINI_MODELO", "gemini-2.5-flash"),
            anthropic_api_key=env("ANTHROPIC_API_KEY") or None,
            anthropic_modelo=env("ANTHROPIC_MODELO", "claude-sonnet-5-5"),
            confianca_minima=float(env("CONFIANCA_MINIMA", "0.75")),
            slack_webhook_url=env("SLACK_WEBHOOK_URL") or None,
        )