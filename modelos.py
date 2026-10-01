from datetime import date, datetime
from typing import Optional
from pydantic import NaiveDatetime, field_validator
from sqlmodel import SQLModel, Field

TIPOS = ["elétrica", "hidráulica", "informática", "climatização", "mobiliário", "limpeza", "outro"]
LOCAIS = ["Bloco A", "Bloco B", "Laboratórios", "Biblioteca", "Cantina", "Quadra", "Auditório", "Banheiros", "Estacionamento"]
PRIORIDADES = ["baixa", "média", "alta"]


# ---------- Tabelas do banco ----------

class Aluno(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    matricula: str = Field(unique=True, index=True)
    turma: str
    chave: str = Field(unique=True, index=True)
    ativo: bool = True
    criado_em: NaiveDatetime = Field(default_factory=datetime.now)


class Chamado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    aluno_id: int = Field(foreign_key="aluno.id", index=True)
    titulo: str
    descricao: str = ""
    tipo: str
    local: str
    prioridade: str
    data_abertura: date
    status: str = "aberto"
    responsavel: Optional[str] = None
    solucao: Optional[str] = None
    data_resolucao: Optional[date] = None


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    aluno_id: Optional[int] = Field(default=None, index=True)
    metodo: str
    rota: str
    status_code: int
    ip: str = ""
    quando: NaiveDatetime = Field(default_factory=datetime.now)


# ---------- O que entra e sai da API ----------

class ChamadoEntrada(SQLModel):
    titulo: str = Field(min_length=3, max_length=80)
    descricao: str = Field(default="", max_length=500)
    tipo: str
    local: str
    prioridade: str
    data_abertura: date

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, valor):
        if valor not in TIPOS:
            raise ValueError("Tipo inválido. Use um de: " + ", ".join(TIPOS))
        return valor

    @field_validator("local")
    @classmethod
    def validar_local(cls, valor):
        if valor not in LOCAIS:
            raise ValueError("Local inválido. Use um de: " + ", ".join(LOCAIS))
        return valor

    @field_validator("prioridade")
    @classmethod
    def validar_prioridade(cls, valor):
        if valor not in PRIORIDADES:
            raise ValueError("Prioridade inválida. Use uma de: " + ", ".join(PRIORIDADES))
        return valor

    @field_validator("data_abertura")
    @classmethod
    def validar_data(cls, valor):
        if valor > date.today():
            raise ValueError("A data não pode estar no futuro")
        return valor


class ChamadoSaida(SQLModel):
    id: int
    titulo: str
    descricao: str
    tipo: str
    local: str
    prioridade: str
    data_abertura: date
    status: str
    responsavel: Optional[str]
    solucao: Optional[str]
    data_resolucao: Optional[date]


class Inicio(SQLModel):
    responsavel: str = Field(min_length=3, max_length=80)


class Resolucao(SQLModel):
    solucao: str = Field(min_length=3, max_length=300)


class AlunoEntrada(SQLModel):
    nome: str
    matricula: str
    turma: str


class Ativacao(SQLModel):
    ativo: bool
