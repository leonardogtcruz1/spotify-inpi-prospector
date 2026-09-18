#!/bin/bash
# Duplo clique no Mac para executar a automação
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

bash run.sh

echo ""
echo "--------------------------------------------------"
echo "Processo finalizado! A planilha está na pasta output/."
echo "Pressione ENTER para fechar esta janela..."
read
