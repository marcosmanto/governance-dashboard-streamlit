
@echo off
REM Inicia o backend (Uvicorn) a partir da raiz do projeto
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src
uvicorn backend.main:app --reload
