"""API REST do MediFlow (FastAPI)"""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.dependencias import montar_servico
from app.modelos.entrada import PLACEHOLDER_IMAGEM, DocumentoEntrada
from app.modelos.saida import DecisaoAuditoria, RespostaTriagem
from app.servicos.armazenamento import ErroArmazenamento
from app.servicos.llm import Anexo
from app.servicos.triagem import DocumentoDuplicado, DocumentoNaoEncontrado, TriagemServico

logging.basicConfig(level=logging.INFO)
MIMES = {"application/app": "PDF", "image/png": "IMAGEM", "image/jpeg": "IMAGEM", "image/webp": "IMAGEM"}
LIMITE_BYTES = 10 * 1024 * 1024

def _traduzir(erro: dict) -> str:
    tipo, msg = erro.get("type", ""), erro.get("type", ""), erro.get("msg", "")
    if tipo == "missing":
        return "campo obrigatório"
    if tipo == "value_error":
        return msg.removeprefix("Value error, ")
    if tipo == "json_invalid":
        return "JSON inválido"
    if tipo.endswith("_type") or tipo.endswith("_parsing"):
        return "tipo de dado inválido"
    if tipo == "literal_error":
        return "valor não permitido"
    return msg

def _detalhes(erros) -> list[dict]:
    return [
        {"campo": ".".join(str(p) for p in e ["loc"] if p not in ("body", "form")) or "corpo",
         "mensagem": _traduzir(e)}
        for e in erros
    ]


def criar_app(servico: TriagemServico | None = None) -> FastAPI:
    app = FastAPI(title="MediFlow", version="1.0.0",
                  description="Agente autônomo para triagem, extração e roteamento de documentos clínicos")
    app.state.servico = servico

    def obter_servico(request: Request) -> TriagemServico:
        if request.app.state.servico is None:
            request.app.state.servico = montar_servico()
        return request.app.state.servico

    @app.exception_handler(RequestValidationError)
    async def _422(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": _detalhes(exc.errors())})

    @app.exception_handler(DocumentoDuplicado)
    async def _409(_: Request, exc: DocumentoDuplicado):
        return JSONResponse(status_code=409, content={
            "detail": f"O documento '{exc.documento_id}' já foi recebido (existe em recebidos/)."})

    @app.exception_handler(DocumentoNaoEncontrado)
    async def _404(_: Request, exc: DocumentoNaoEncontrado):
        return JSONResponse(status_code=404, content={"detail": "Documento não encontrado."})

    @app.exception_handler(ErroArmazenamento)
    async def _503(_: Request, exc: ErroArmazenamento):
        return JSONResponse(status_code=503, content={
            "detail": f"Armazenamento indisponível: {exc}"})

    @app.get("/saude")
    def saude():
        return {"status": "ok"}

    @app.post("/triagem", response_model=RespostaTriagem)
    def triagem(doc: DocumentoEntrada, servico: TriagemServico = Depends(obter_servico)):
        return servico.processar(doc)

    @app.post("/triagem/arquivo", response_model=RespostaTriagem)
    def triagem_arquivo(
        documento_id: str = Form(...),
        canal_origem: str | None = Form(None),
        arquivo: UploadFile = File(...),
        servico: TriagemServico = Depends(obter_servico),
    ):
        mime = arquivo.content_type or ""
        if mime not in MIMES:
            raise HTTPException(415, "Formato não suportado. Envie PDF, PNG, JPEG ou WEBP.")
        conteudo = arquivo.file.read(LIMITE_BYTES + 1)
        if len(conteudo) > LIMITE_BYTES:
            raise HTTPException(413, "Arquivo maior que 10 MB.")

        texto = ""
        if mime == "application/pdf":
            try:
                import io
                from pypdf import PdfReader

                texto = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(conteudo)).pages)
            except Exception:
                texto = ""  # PDF digitalizado: o LLM multimodal lê o anexo
        try:
            doc = DocumentoEntrada(
                documento_id=documento_id, tipo_arquivo=MIMES[mime],
                documento_texto=texto.strip() or PLACEHOLDER_IMAGEM, canal_origem=canal_origem,
            )
        except ValidationError as exc:
            return JSONResponse(status_code=422, content={"detail": _detalhes(exc.errors())})
        return servico.processar(doc, Anexo(conteudo, mime))

    @app.get("/triagem/{documento_id}", response_model=RespostaTriagem)
    def consultar(documento_id: str, servico: TriagemServico = Depends(obter_servico)):
        return servico.obter(documento_id)

    @app.get("/historico")
    def historico(servico: TriagemServico = Depends(obter_servico)):
        return servico.historico()

    @app.get("/auditoria")
    def pendentes(servico: TriagemServico = Depends(obter_servico)):
        return {"pendentes": servico.pendentes_auditoria()}

    @app.post("/auditoria/{documento_id}/decisao")
    def decidir(documento_id: str, decisao: DecisaoAuditoria,
                servico: TriagemServico = Depends(obter_servico)):
        servico.registrar_decisao(documento_id, decisao)
        return {"documento_id": documento_id, "decisao": decisao.decisao}

    return app


app = criar_app()
