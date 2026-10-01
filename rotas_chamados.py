from datetime import date
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_, func
from banco import get_sessao
from modelos import Aluno, Chamado, ChamadoEntrada, ChamadoSaida, Inicio, Resolucao, TIPOS, LOCAIS, PRIORIDADES
from seguranca import aluno_atual

router = APIRouter()

LIMITE_CHAMADOS = 100


def buscar_chamado_do_aluno(id: int, aluno: Aluno, sessao: Session):
    chamado = sessao.get(Chamado, id)
    if not chamado or chamado.aluno_id != aluno.id:
        raise HTTPException(404, "Chamado não encontrado")
    return chamado


def salvar(chamado: Chamado, sessao: Session):
    sessao.add(chamado)
    sessao.commit()
    sessao.refresh(chamado)
    return chamado


@router.get("/eu", tags=["Aluno"])
def quem_sou_eu(aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    total = sessao.exec(select(func.count(Chamado.id)).where(Chamado.aluno_id == aluno.id)).one()
    return {"nome": aluno.nome, "matricula": aluno.matricula, "turma": aluno.turma, "total_chamados": total}


@router.get("/tipos", tags=["Listas"])
def listar_tipos(aluno: Aluno = Depends(aluno_atual)):
    return TIPOS


@router.get("/locais", tags=["Listas"])
def listar_locais(aluno: Aluno = Depends(aluno_atual)):
    return LOCAIS


@router.get("/prioridades", tags=["Listas"])
def listar_prioridades(aluno: Aluno = Depends(aluno_atual)):
    return PRIORIDADES


@router.get("/chamados", response_model=list[ChamadoSaida], tags=["Chamados"])
def listar_chamados(
    status: Optional[Literal["aberto", "em andamento", "resolvido"]] = None,
    tipo: Optional[str] = None,
    local: Optional[str] = None,
    prioridade: Optional[Literal["baixa", "média", "alta"]] = None,
    busca: Optional[str] = None,
    aluno: Aluno = Depends(aluno_atual),
    sessao: Session = Depends(get_sessao),
):
    consulta = select(Chamado).where(Chamado.aluno_id == aluno.id)
    if status:
        consulta = consulta.where(Chamado.status == status)
    if tipo:
        consulta = consulta.where(Chamado.tipo == tipo)
    if local:
        consulta = consulta.where(Chamado.local == local)
    if prioridade:
        consulta = consulta.where(Chamado.prioridade == prioridade)
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(or_(Chamado.titulo.ilike(termo), Chamado.descricao.ilike(termo)))
    consulta = consulta.order_by(Chamado.data_abertura.desc(), Chamado.id.desc())
    return sessao.exec(consulta).all()


@router.get("/chamados/{id}", response_model=ChamadoSaida, tags=["Chamados"])
def detalhar_chamado(id: int, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    return buscar_chamado_do_aluno(id, aluno, sessao)


@router.post("/chamados", response_model=ChamadoSaida, status_code=201, tags=["Chamados"])
def abrir_chamado(dados: ChamadoEntrada, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    total = sessao.exec(select(func.count(Chamado.id)).where(Chamado.aluno_id == aluno.id)).one()
    if total >= LIMITE_CHAMADOS:
        raise HTTPException(400, f"Limite de {LIMITE_CHAMADOS} chamados atingido")
    return salvar(Chamado(**dados.model_dump(), aluno_id=aluno.id), sessao)


@router.put("/chamados/{id}", response_model=ChamadoSaida, tags=["Chamados"])
def editar_chamado(id: int, dados: ChamadoEntrada, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    chamado = buscar_chamado_do_aluno(id, aluno, sessao)
    if chamado.status == "resolvido":
        raise HTTPException(400, "Chamado resolvido não pode ser editado")
    for campo, valor in dados.model_dump().items():
        setattr(chamado, campo, valor)
    return salvar(chamado, sessao)


@router.patch("/chamados/{id}/iniciar", response_model=ChamadoSaida, tags=["Chamados"])
def iniciar_atendimento(id: int, dados: Inicio, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    chamado = buscar_chamado_do_aluno(id, aluno, sessao)
    if chamado.status != "aberto":
        raise HTTPException(400, "Só é possível iniciar um chamado aberto")
    chamado.status = "em andamento"
    chamado.responsavel = dados.responsavel
    return salvar(chamado, sessao)


@router.patch("/chamados/{id}/resolver", response_model=ChamadoSaida, tags=["Chamados"])
def resolver_chamado(id: int, dados: Resolucao, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    chamado = buscar_chamado_do_aluno(id, aluno, sessao)
    if chamado.status != "em andamento":
        raise HTTPException(400, "Só é possível resolver um chamado em andamento")
    chamado.status = "resolvido"
    chamado.solucao = dados.solucao
    chamado.data_resolucao = date.today()
    return salvar(chamado, sessao)


@router.delete("/chamados/{id}", status_code=204, tags=["Chamados"])
def excluir_chamado(id: int, aluno: Aluno = Depends(aluno_atual), sessao: Session = Depends(get_sessao)):
    chamado = buscar_chamado_do_aluno(id, aluno, sessao)
    sessao.delete(chamado)
    sessao.commit()
