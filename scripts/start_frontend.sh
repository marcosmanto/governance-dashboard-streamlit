
#!/usr/bin/env bash
set -euo pipefail
# Inicia o frontend (Streamlit) a partir da raiz do projeto
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
exec streamlit run frontend/app.py
``
