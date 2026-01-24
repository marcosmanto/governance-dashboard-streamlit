from typing import List

from fastapi import FastAPI

from backend.crud import (
    atualizar_registro,
    deletar_registro,
    inserir_registro,
    listar_registros,
)
from backend.models import RegistroIn, RegistroOut

app = FastAPI(title="API Painel de Dados")


@app.get("/registros", response_model=List[RegistroOut])
def get_registros():
    return listar_registros()


@app.post("/registros", status_code=201)
def post_registro(registro: RegistroIn):
    inserir_registro(registro)
    return {"message": "Registro inserido com sucesso"}


@app.put("/registros/{id_}")
def put_registro(id_: int, registro: RegistroIn):
    atualizar_registro(id_, registro)
    return {"message": "Registro atualizado com sucesso"}


@app.delete("/registros/{id_}")
def delete_registro(id_: int):
    deletar_registro(id_)
    return {"message": "Registro excluído com sucesso"}
