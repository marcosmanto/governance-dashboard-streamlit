from typing import List

from fastapi import FastAPI, HTTPException

from backend.crud import (
    atualizar_registro,
    deletar_registro,
    listar_registros,
    # inserir_registro,
    upsert_registro,
)
from backend.db.errors import DuplicateKeyError
from backend.models import RegistroIn, RegistroOut

app = FastAPI(title="API Painel de Dados")


@app.get("/registros", response_model=List[RegistroOut])
def get_registros():
    return listar_registros()


@app.post("/registros", status_code=201)
def post_registro(registro: RegistroIn):
    try:
        # inserir_registro(registro)
        upsert_registro(registro)
        return {"message": "Registro inserido/atualizado (UPSERT) com sucesso"}
    except DuplicateKeyError:
        # Só ocorreria se você usar INSERT direto na tabela sem view, por exemplo.
        raise HTTPException(status_code=409, detail="Duplicidade em (data, categoria)")


@app.put("/registros/{id_}")
def put_registro(id_: int, registro: RegistroIn):
    ok = atualizar_registro(id_, registro)
    if not ok:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return {"message": "Registro atualizado com sucesso"}


@app.delete("/registros/{id_}")
def delete_registro(id_: int):
    deletar_registro(id_)
    return {"message": "Registro excluído com sucesso"}
