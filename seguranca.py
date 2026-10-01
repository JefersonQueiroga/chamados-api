import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session, select
from banco import get_sessao
from modelos import Aluno

load_dotenv()

CHAVE_PROFESSOR = os.getenv("CHAVE_PROFESSOR", "")
cabecalho_chave = APIKeyHeader(name="X-API-Key", auto_error=False)


def aluno_atual(chave: str = Security(cabecalho_chave), sessao: Session = Depends(get_sessao)):
    if not chave:
        raise HTTPException(401, "Envie sua chave no cabeçalho X-API-Key")
    aluno = sessao.exec(select(Aluno).where(Aluno.chave == chave)).first()
    if not aluno or not aluno.ativo:
        raise HTTPException(401, "Chave inválida ou desativada")
    return aluno


def professor(chave: str = Security(cabecalho_chave)):
    if not CHAVE_PROFESSOR or chave != CHAVE_PROFESSOR:
        raise HTTPException(403, "Acesso restrito ao professor")
