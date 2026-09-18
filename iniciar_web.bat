@echo off
cd /d "%~dp0"
echo ======================================================================
echo   INICIANDO PAINEL WEB SPOTIFY & INPI PROSPECTOR
echo ======================================================================

if not exist ".venv" (
    echo Configurando ambiente pela primeira vez na maquina...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

start "" "http://localhost:8000"
echo Abrindo o painel no seu navegador: http://localhost:8000
echo Para encerrar o servidor, feche esta janela ou pressione Ctrl+C.
echo ----------------------------------------------------------------------
python web_server.py
pause
