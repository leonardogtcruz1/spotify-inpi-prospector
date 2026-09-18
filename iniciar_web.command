#!/bin/bash
# Duplo clique no Mac para iniciar o painel web
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo "  INICIANDO PAINEL WEB SPOTIFY & INPI PROSPECTOR"
echo "======================================================================"

if [ ! -d ".venv" ]; then
    echo "Configurando ambiente pela primeira vez na sua maquina..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
else
    source .venv/bin/activate
fi

# Abre o navegador automaticamente apos 1.5s
(sleep 1.5 && open "http://localhost:8000") &

echo "Abrindo o painel no seu navegador: http://localhost:8000"
echo "Para encerrar o servidor, feche esta janela ou pressione Ctrl+C."
echo "----------------------------------------------------------------------"
python3 web_server.py
