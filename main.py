import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from banco import engine, criar_tabelas
from modelos import Aluno, Log
import rotas_chamados
import rotas_admin

LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "60"))
ROTAS_SEM_LOG = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]


@asynccontextmanager
async def ao_iniciar(app: FastAPI):
    criar_tabelas()
    yield


app = FastAPI(
    title="API Chamados de Manutenção IFRN",
    description="Envie sua chave no cabeçalho **X-API-Key**. Aqui no /docs, clique em **Authorize** e cole a chave.",
    version="1.0",
    lifespan=ao_iniciar,
)

acessos = defaultdict(list)


def passou_do_limite(chave: str):
    agora = time.time()
    acessos[chave] = [momento for momento in acessos[chave] if agora - momento < 60]
    acessos[chave].append(agora)
    return len(acessos[chave]) > LIMITE_POR_MINUTO


@app.middleware("http")
async def registrar_requisicao(request: Request, call_next):
    chave = request.headers.get("X-API-Key")
    if chave and passou_do_limite(chave):
        resposta = JSONResponse({"detail": "Muitas requisições. Espere um minuto."}, status_code=429)
    else:
        resposta = await call_next(request)

    if request.method != "OPTIONS" and request.url.path not in ROTAS_SEM_LOG:
        ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
        with Session(engine) as sessao:
            aluno = sessao.exec(select(Aluno).where(Aluno.chave == chave)).first() if chave else None
            sessao.add(Log(
                aluno_id=aluno.id if aluno else None,
                metodo=request.method,
                rota=request.url.path,
                status_code=resposta.status_code,
                ip=ip,
            ))
            sessao.commit()
    return resposta


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
)


@app.get("/", tags=["Status"])
def status():
    return {"api": "Chamados de Manutenção IFRN", "status": "ok", "documentacao": "/docs"}


app.include_router(rotas_chamados.router)
app.include_router(rotas_admin.router)
