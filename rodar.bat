@echo off
chcp 65001 >nul
cd /d "%~dp0"
title API Chamados de Manutencao IFRN

where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
  pause
  exit /b
)

if not exist .venv (
  echo Criando ambiente virtual...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo Instalando dependencias...
python -m pip install -q -r requirements.txt

if not exist .env (
  copy .env.exemplo .env >nul
  python -c "import secrets;p='.env';s=open(p,encoding='utf-8').read();open(p,'w',encoding='utf-8').write(s.replace('troque-por-uma-chave-grande-e-secreta',secrets.token_urlsafe(24)))"
  echo Arquivo .env criado com uma CHAVE_PROFESSOR aleatoria.
)

if not exist chamados.db (
  start "" /b cmd /c "timeout /t 6 >nul & python professor.py cadastrar turma_exemplo.csv"
)
start "" /b cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000/docs"

echo.
echo API rodando em http://127.0.0.1:8000/docs  (feche esta janela para parar)
echo.
python -m uvicorn main:app --reload
