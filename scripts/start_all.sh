
#!/usr/bin/env bash
set -euo pipefail
# Inicia backend e frontend; encerra backend ao sair
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

uvicorn backend.main:app --reload &
BACK_PID=$!
cleanup(){ kill "$BACK_PID" 2>/dev/null || true; }
trap cleanup EXIT

# Opcional: aguarda backend subir se curl existir
READY=0
if command -v curl >/dev/null 2>&1; then
  for i in {1..30}; do
    if curl -fsS http://127.0.0.1:8000/docs >/dev/null 2>&1; then READY=1; break; fi
    sleep 0.3
  done
fi
[ "$READY" -eq 1 ] && echo "[ok] backend no ar em http://127.0.0.1:8000" || echo "[info] seguindo sem checar disponibilidade do backend"

# Streamlit em primeiro plano
exec streamlit run frontend/Home.py
``
