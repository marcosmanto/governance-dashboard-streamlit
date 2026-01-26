
#!/usr/bin/env bash
set -euo pipefail
# Inicia o backend (Uvicorn) a partir da raiz do projeto
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
exec uvicorn backend.main:app --reload
