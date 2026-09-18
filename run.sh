#!/bin/bash
# Atalho de execução para o automador de planilha Top 50

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Se o ambiente virtual ainda não existir, cria e instala dependências automaticamente
if [ ! -d ".venv" ]; then
    echo "======================================================================"
    echo "  Configurando o robô pela primeira vez na sua máquina..."
    echo "  (Isso só acontece na 1ª vez e leva menos de 1 minuto)"
    echo "======================================================================"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
else
    source .venv/bin/activate
fi

python3 automator.py "$@"
