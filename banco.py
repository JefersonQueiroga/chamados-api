import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()

URL_BANCO = os.getenv("URL_BANCO", "sqlite:///chamados.db")
engine = create_engine(URL_BANCO, connect_args={"check_same_thread": False})


def criar_tabelas():
    SQLModel.metadata.create_all(engine)


def get_sessao():
    with Session(engine) as sessao:
        yield sessao
