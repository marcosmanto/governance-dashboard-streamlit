from backend.crud import listar_registros
from fastapi import FastAPI

app = FastAPI(title="API Painel de Dados")


@app.get("/registros")
def get_registros():
    return listar_registros()
