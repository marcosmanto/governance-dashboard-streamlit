
@echo off
REM Abre backend e frontend em janelas separadas do CMD
cd /d "%~dp0\.."
set "PYTHONPATH=%CD%"
start "Uvicorn (backend)" cmd /k "set PYTHONPATH=%CD% && uvicorn backend.main:app --reload"
start "Streamlit (frontend)" cmd /k "set PYTHONPATH=%CD% && streamlit run frontend\Home.py"
echo [OK] Backend e frontend foram iniciados em janelas separadas.
