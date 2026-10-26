# app/storage.py
# Objetivo: salvar arquivos em "buckets". Local por padrão; OCI quando configurado.
import os
import json
import pathlib
from dotenv import load_dotenv

load_dotenv(override=True)

BUCKET = os.getenv("OCI_BUCKET", "mediflow-documentos-clinicos")

def _salvar_local(caminho: str, dados: bytes):
    # Cria storage_local/<bucket>/<caminho>, criando as pastas que faltarem
    destino = pathlib.Path("storage_local") / BUCKET / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)

def _salvar_oci(namespace: str, caminho: str, dados: bytes):
    import oci   # importado aqui para só ser exigido quando o OCI for usado
    config = oci.config.from_file(os.path.expanduser(
        os.getenv("OCI_CONFIG_FILE", "~/.oci/config")))
    cliente = oci.object_storage.ObjectStorageClient(config)
    cliente.put_object(namespace, BUCKET, caminho, dados)

def salvar(caminho: str, conteudo) -> dict:
    """Salva texto ou dicionário. Devolve onde e como foi salvo."""
    # Dicionário vira JSON legível; texto fica como está
    texto = conteudo if isinstance(conteudo, str) else json.dumps(
        conteudo, ensure_ascii=False, indent=2)
    dados = texto.encode("utf-8")
    namespace = os.getenv("OCI_NAMESPACE")

    if namespace:                       # OCI configurado: tenta nuvem
        try:
            _salvar_oci(namespace, caminho, dados)
            return {"bucket": BUCKET, "caminho_objeto": caminho,
                    "local": "oci", "status_backup": "sucesso"}
        except Exception as e:          # falhou: não perde o documento
            _salvar_local(caminho, dados)
            return {"bucket": BUCKET, "caminho_objeto": caminho, "local": "disco",
                    "status_backup": f"oci_falhou_salvo_local: {str(e)[:80]}"}

    _salvar_local(caminho, dados)       # sem OCI: salva no disco
    return {"bucket": BUCKET, "caminho_objeto": caminho,
            "local": "disco", "status_backup": "sucesso"}