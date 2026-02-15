import logging
from datetime import date
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request

from backend.audit.middleware import AuditMiddleware
from backend.audit.service import registrar_evento
from backend.audit.verify import verificar_integridade_auditoria
from backend.auth.dependencies import get_current_user
from backend.auth.jwt import decode_token
from backend.auth.permissions import require_role
from backend.auth.service import (
    cleanup_expired_sessions,
    cleanup_revoked_sessions,
    issue_new_access_token,
    login_user,
    logout_session,
    revoke_all_sessions,
    revoke_session_by_id,
)
from backend.core.config import settings
from backend.core.exceptions import register_exception_handlers
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
from backend.db import connect
from backend.db.errors import DuplicateKeyError
from backend.models import AuditoriaOut, RegistroIn, RegistroOut, User, UserLoginOut
from backend.users.admin import router as admin_router
from backend.users.service import authenticate_user
from backend.users.users import router as users_router

app = FastAPI(title="Governance Dashboard API")

logger = logging.getLogger("auth-debug")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

if settings.ENV == "dev":
    register_exception_handlers(app, logger)

app.add_middleware(AuditMiddleware)
# 🔐 Rotas administrativas
app.include_router(admin_router)
# 🔓 Rotas públicas
app.include_router(users_router)


@app.get("/registros", response_model=List[RegistroOut])
def get_registros():  # user: User = Depends(get_current_user)):
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
    user: User = Depends(get_current_user),
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


@app.post("/logout")
def logout(user=Depends(get_current_user)):
    logout_session(user.session_id)
    return {"message": "Logout realizado com sucesso"}


@app.post("/login", response_model=UserLoginOut)
def login(username: str, password: str):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token, refresh_token = login_user(
        user["username"],
        user["role"],
    )

    if user["must_change_password"]:
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "must_change_password": True,
            "user": None,
        }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
        "must_change_password": False,
    }


@app.post("/refresh")
def refresh_token(payload: dict = Depends(decode_token)):
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        usertokens = issue_new_access_token(payload)
        return usertokens
    except Exception:
        # detail=str(e) => Nunca exponha str(e). Pode acabar expondo: Erros internos, mensagens de banco, Stack trace parcial
        raise HTTPException(status_code=401, detail="REFRESH_FAILED")


@app.post("/admin/users/{username}/sessions/revoke")
def revoke_user_sessions(username: str, user: User = Depends(get_current_user)):
    require_role("admin")(user)
    revoke_all_sessions(username)
    return {"message": f"Sessões de {username} revogadas com sucesso"}


@app.post("/admin/sessions/{session_id}/revoke")
def revoke_single_session(
    session_id: str,
    user=Depends(get_current_user),
):
    require_role("admin")(user)
    revoke_session_by_id(session_id)
    return {"message": "Sessão revogada"}


@app.post("/admin/sessions/cleanup")
def cleanup_sessions(user=Depends(get_current_user)):
    require_role("admin")(user)
    count = cleanup_expired_sessions()
    return {
        "deleted_sessions": count,
        "message": "Sessões expiradas foram excluídas com sucesso",
    }


@app.post("/admin/sessions/revoked/cleanup")
def cleanup_sessions_revoked(user=Depends(get_current_user)):
    require_role("admin")(user)
    count = cleanup_revoked_sessions()
    return {
        "deleted_sessions": count,
        "message": "Sessões revogadas foram excluídas com sucesso",
    }


@app.get("/admin/audit/verify")
def verify_audit_chain(user=Depends(get_current_user)):
    require_role("admin")(user)
    conn = connect()
    try:
        return verificar_integridade_auditoria(conn)
    finally:
        conn.close()
