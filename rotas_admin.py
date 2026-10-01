import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, delete
from banco import get_sessao
from dados_iniciais import sortear_chamados, QUANTIDADE_INICIAL
from modelos import Aluno, Chamado, Log, AlunoEntrada, Ativacao
from seguranca import professor

router = APIRouter(prefix="/admin", dependencies=[Depends(professor)], include_in_schema=False)


def buscar_aluno(matricula: str, sessao: Session):
    aluno = sessao.exec(select(Aluno).where(Aluno.matricula == matricula)).first()
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    return aluno


def resumo(aluno: Aluno, sessao: Session):
    total_chamados = sessao.exec(select(func.count(Chamado.id)).where(Chamado.aluno_id == aluno.id)).one()
    ultima = sessao.exec(select(func.max(Log.quando)).where(Log.aluno_id == aluno.id)).one()
    return {
        "nome": aluno.nome,
        "matricula": aluno.matricula,
        "turma": aluno.turma,
        "chave": aluno.chave,
        "ativo": aluno.ativo,
        "total_chamados": total_chamados,
        "ultima_requisicao": ultima,
    }


@router.post("/alunos")
def cadastrar_alunos(alunos: list[AlunoEntrada], sessao: Session = Depends(get_sessao)):
    resultado = []
    for dados in alunos:
        aluno = sessao.exec(select(Aluno).where(Aluno.matricula == dados.matricula)).first()
        novo = aluno is None
        if novo:
            aluno = Aluno(**dados.model_dump(), chave=secrets.token_urlsafe(16))
            sessao.add(aluno)
            sessao.commit()
            sessao.refresh(aluno)
            sessao.add_all(sortear_chamados(aluno))
            sessao.commit()
        resultado.append({"nome": aluno.nome, "matricula": aluno.matricula, "turma": aluno.turma, "chave": aluno.chave, "novo": novo})
    return resultado


@router.get("/alunos")
def listar_alunos(sessao: Session = Depends(get_sessao)):
    alunos = sessao.exec(select(Aluno).order_by(Aluno.turma, Aluno.nome)).all()
    return [resumo(aluno, sessao) for aluno in alunos]


@router.get("/alunos/{matricula}/uso")
def uso_do_aluno(matricula: str, sessao: Session = Depends(get_sessao)):
    aluno = buscar_aluno(matricula, sessao)
    logs = sessao.exec(select(Log).where(Log.aluno_id == aluno.id)).all()
    por_metodo = {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}
    dias = set()
    for log in logs:
        if log.metodo in por_metodo:
            por_metodo[log.metodo] += 1
        dias.add(log.quando.date().isoformat())
    return {**resumo(aluno, sessao), "total_requisicoes": len(logs), "por_metodo": por_metodo, "dias_de_uso": sorted(dias)}


@router.get("/logs")
def listar_logs(matricula: Optional[str] = None, limite: int = 100, sessao: Session = Depends(get_sessao)):
    consulta = select(Log, Aluno.nome).join(Aluno, Log.aluno_id == Aluno.id, isouter=True)
    if matricula:
        aluno = buscar_aluno(matricula, sessao)
        consulta = consulta.where(Log.aluno_id == aluno.id)
    consulta = consulta.order_by(Log.id.desc()).limit(limite)
    return [{**log.model_dump(), "aluno": nome} for log, nome in sessao.exec(consulta).all()]


@router.post("/alunos/{matricula}/nova-chave")
def trocar_chave(matricula: str, sessao: Session = Depends(get_sessao)):
    aluno = buscar_aluno(matricula, sessao)
    aluno.chave = secrets.token_urlsafe(16)
    sessao.add(aluno)
    sessao.commit()
    return {"matricula": aluno.matricula, "chave": aluno.chave}


@router.patch("/alunos/{matricula}/ativo")
def ativar_ou_bloquear(matricula: str, dados: Ativacao, sessao: Session = Depends(get_sessao)):
    aluno = buscar_aluno(matricula, sessao)
    aluno.ativo = dados.ativo
    sessao.add(aluno)
    sessao.commit()
    return {"matricula": aluno.matricula, "ativo": aluno.ativo}


@router.post("/alunos/{matricula}/resetar")
def resetar_chamados(matricula: str, sessao: Session = Depends(get_sessao)):
    aluno = buscar_aluno(matricula, sessao)
    sessao.exec(delete(Chamado).where(Chamado.aluno_id == aluno.id))
    sessao.add_all(sortear_chamados(aluno))
    sessao.commit()
    return {"matricula": aluno.matricula, "total_chamados": QUANTIDADE_INICIAL}
