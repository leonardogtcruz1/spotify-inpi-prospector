import sys
import os

# Adiciona o diretório raiz ao sys.path para permitir imports de módulos locais
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from web_server import app
