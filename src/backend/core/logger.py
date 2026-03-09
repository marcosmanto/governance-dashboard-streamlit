import logging
import sys

# Configuração centralizada do logger de autenticação
logger = logging.getLogger("auth-debug")
logger.setLevel(logging.INFO)

# Garante que o handler seja adicionado apenas uma vez
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
