# API Chamados de Manutenção IFRN

API em FastAPI para os alunos consumirem no front-end React. Cada aluno tem uma chave própria e só enxerga os próprios chamados.

## Rodar no computador (Windows)

Jeito rápido: dê dois cliques em `rodar.bat`.

Passo a passo manual:

```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.exemplo .env
uvicorn main:app --reload
```

Troque `CHAVE_PROFESSOR` no `.env` antes de rodar. Documentação: http://127.0.0.1:8000/docs

## Cadastrar a turma

Com a API rodando, em outro terminal:

```
python professor.py cadastrar turma.csv
```

As chaves ficam em `chaves.csv`. Outros comandos: `python professor.py` (alunos, uso, logs, nova-chave, resetar, bloquear, desbloquear).

## Arquivos

| Arquivo | O que tem |
| --- | --- |
| `main.py` | cria a API, CORS, registro de requisições e limite por minuto |
| `banco.py` | conexão com o SQLite |
| `modelos.py` | tabelas (Aluno, Chamado, Log) e validações |
| `seguranca.py` | verificação da chave do aluno e do professor |
| `rotas_chamados.py` | rotas que os alunos usam |
| `rotas_admin.py` | rotas do professor (não aparecem no /docs) |
| `dados_iniciais.py` | sorteio dos 8 chamados iniciais de cada aluno |
| `professor.py` | comandos do professor pelo terminal |

## Rotas dos alunos

Todas exigem o cabeçalho `X-API-Key`.

| Método | Rota | O que faz |
| --- | --- | --- |
| GET | `/eu` | dados do dono da chave |
| GET | `/chamados` | lista (filtros: `status`, `tipo`, `local`, `prioridade`, `busca`) |
| GET | `/chamados/{id}` | detalhe |
| POST | `/chamados` | abre um chamado (status começa como "aberto") |
| PUT | `/chamados/{id}` | edita (não vale para chamado resolvido) |
| PATCH | `/chamados/{id}/iniciar` | aberto → em andamento (informa o responsável) |
| PATCH | `/chamados/{id}/resolver` | em andamento → resolvido (informa a solução) |
| DELETE | `/chamados/{id}` | remove |
| GET | `/tipos`, `/locais`, `/prioridades` | listas para os selects |

## Publicar na VPS

1. No DNS, crie um registro **A** `api-chamados` apontando para o IP da VPS.
2. Na VPS:

```
git clone https://github.com/JefersonQueiroga/chamados-api.git /opt/chamados-api
bash /opt/chamados-api/deploy.sh
```

3. No `.env` do seu computador: `URL_API=https://api-chamados.jefersonqueiroga.com.br` e a `CHAVE_PROFESSOR` mostrada pelo script. Depois: `python professor.py cadastrar turma.csv`.

Para atualizar: `cd /opt/chamados-api && git pull && bash deploy.sh`
