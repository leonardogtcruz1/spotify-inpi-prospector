@echo off
cd /d "%~dp0"
echo ======================================================================
echo   AUTOMATIZADOR DE PLANILHAS TOP 50 SPOTIFY - PROSPECCAO DE MARCAS
echo ======================================================================
if not exist ".venv" (
    echo Configurando ambiente pela primeira vez na maquina...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)
python automator.py %*
echo.
echo --------------------------------------------------
echo Processo finalizado! A planilha esta na pasta output.
pause
