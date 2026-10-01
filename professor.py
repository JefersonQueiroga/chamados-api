import csv
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

URL_API = os.getenv("URL_API", "http://127.0.0.1:8000")
cliente = httpx.Client(base_url=URL_API, headers={"X-API-Key": os.getenv("CHAVE_PROFESSOR", "")}, timeout=30)

AJUDA = """
Uso: python professor.py <comando> [argumento]

  cadastrar turma.csv     cadastra alunos (colunas: nome,matricula,turma) e gera chaves.csv
  alunos                  lista alunos, chaves e total de chamados
  uso MATRICULA           mostra quantas vezes o aluno usou cada método
  logs [MATRICULA]        últimas 30 requisições
  nova-chave MATRICULA    troca a chave do aluno
  resetar MATRICULA       apaga os chamados do aluno e sorteia de novo
  bloquear MATRICULA      desativa a chave
  desbloquear MATRICULA   reativa a chave
"""


def pedir(metodo, rota, **kwargs):
    resposta = cliente.request(metodo, rota, **kwargs)
    if resposta.status_code >= 400:
        print(f"Erro {resposta.status_code}: {resposta.text}")
        sys.exit(1)
    return resposta.json()


def cadastrar(arquivo):
    with open(arquivo, encoding="utf-8-sig") as f:
        alunos = list(csv.DictReader(f))
    resultado = pedir("POST", "/admin/alunos", json=alunos)
    with open("chaves.csv", "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=["nome", "matricula", "turma", "chave", "novo"])
        escritor.writeheader()
        escritor.writerows(resultado)
    novos = sum(1 for aluno in resultado if aluno["novo"])
    print(f"{novos} aluno(s) novo(s), {len(resultado) - novos} já existiam. Chaves salvas em chaves.csv")


def listar_alunos():
    for aluno in pedir("GET", "/admin/alunos"):
        situacao = "" if aluno["ativo"] else "  [BLOQUEADO]"
        print(f'{aluno["turma"]:<11} {aluno["matricula"]:<16} {aluno["nome"]:<30} chamados: {aluno["total_chamados"]:<4} chave: {aluno["chave"]}{situacao}')


def mostrar_uso(matricula):
    uso = pedir("GET", f"/admin/alunos/{matricula}/uso")
    print(f'{uso["nome"]} ({uso["matricula"]}) - {uso["total_requisicoes"]} requisições')
    for metodo, quantidade in uso["por_metodo"].items():
        print(f"  {metodo:<7} {quantidade}")
    print("  Dias de uso:", ", ".join(uso["dias_de_uso"]) or "nenhum")


def mostrar_logs(matricula=None):
    parametros = {"limite": 30}
    if matricula:
        parametros["matricula"] = matricula
    for log in pedir("GET", "/admin/logs", params=parametros):
        print(f'{log["quando"][:19]}  {log["status_code"]}  {log["metodo"]:<7} {log["rota"]:<25} {log["aluno"] or "-"}')


comandos = {
    "cadastrar": cadastrar,
    "alunos": listar_alunos,
    "uso": mostrar_uso,
    "logs": mostrar_logs,
    "nova-chave": lambda m: print(pedir("POST", f"/admin/alunos/{m}/nova-chave")),
    "resetar": lambda m: print(pedir("POST", f"/admin/alunos/{m}/resetar")),
    "bloquear": lambda m: print(pedir("PATCH", f"/admin/alunos/{m}/ativo", json={"ativo": False})),
    "desbloquear": lambda m: print(pedir("PATCH", f"/admin/alunos/{m}/ativo", json={"ativo": True})),
}

if len(sys.argv) < 2 or sys.argv[1] not in comandos:
    print(AJUDA)
else:
    comandos[sys.argv[1]](*sys.argv[2:])
