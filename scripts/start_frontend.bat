
@echo off
REM Inicia o frontend (Streamlit) a partir da raiz do projeto
cd /d "%~dp0\.."
set PYTHONPATH=%CD%
streamlit run frontend\Home.py
