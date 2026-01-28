from datetime import date, timezone
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request

from backend.audit.middleware import AuditMiddleware
from backend.audit.service import registrar_evento
from backend.auth.dependencies import get_current_user
from backend.auth.permissions import require_role
from backend.crud import (
    # atualizar_registro,
    atualizar_registro_com_auditoria,
    deletar_registro_com_auditoria,
    # deletar_registro,
    listar_registros,
    obter_registro_por_id,
    # inserir_registro,
    upsert_registro,
)
from backend.crud_auditoria import listar_auditoria
from backend.db.errors import DuplicateKeyError
from backend.models import AuditoriaOut, RegistroIn, RegistroOut, User

app = FastAPI(title="API Painel de Dados")
app.add_middleware(AuditMiddleware)


@app.get("/registros", response_model=List[RegistroOut])
def get_registros(user: User = Depends(get_current_user)):
    return listar_registros()


@app.post("/registros", status_code=201)
def post_registro(
    registro: RegistroIn,
    user: User = Depends(get_current_user),
):
    require_role("editor", "admin")(user)
    try:
        # inserir_registro(registro)
        upsert_registro(registro)
        return {"message": "Registro inserido/atualizado (UPSERT) com sucesso"}
    except DuplicateKeyError:
        # Só ocorreria se você usar INSERT direto na tabela sem view, por exemplo.
        raise HTTPException(status_code=409, detail="Duplicidade em (data, categoria)")


@app.get("/registros/{id_}", response_model=RegistroOut)
def get_registro(
    id_: int,
    # user: User = Depends(get_current_user),
):
    registro = obter_registro_por_id(id_)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return registro


@app.put("/registros/{id_}")
def put_registro(
    id_: int,
    registro: RegistroIn,
    request: Request,
    user: User = Depends(get_current_user),
):
    require_role("editor", "admin")(user)

    resultado = atualizar_registro_com_auditoria(id_, registro)
    if not resultado:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    antes, depois = resultado

    registrar_evento(
        username=user.username,
        role=user.role,
        action="UPDATE",
        resource="registros",
        resource_id=id_,
        payload_before=antes,
        payload_after=depois,
        endpoint=request.url.path,
        method=request.method,
    )
    return {"message": "Registro atualizado com sucesso"}


@app.delete("/registros/{id_}")
def delete_registro(
    id_: int,
    request: Request,
    user: User = Depends(get_current_user),
):
    require_role("admin")(user)

    antes = deletar_registro_com_auditoria(id_)
    if not antes:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    registrar_evento(
        username=user.username,
        role=user.role,
        action="DELETE",
        resource="registros",
        resource_id=id_,
        payload_before=antes,
        payload_after=None,
        endpoint=request.url.path,
        method=request.method,
    )
    return {"message": "Registro excluído com sucesso"}


@app.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return user


@app.get("/auditoria", response_model=List[AuditoriaOut])
def get_auditoria(
    username: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    user: User = Depends(get_current_user),
):
    # 🔐 só admin pode consultar auditoria
    require_role("admin")(user)

    return listar_auditoria(
        username=username,
        action=action,
        resource=resource,
        data_inicio=data_inicio.isoformat() if data_inicio else None,
        data_fim=data_fim.isoformat() if data_fim else None,
    )
