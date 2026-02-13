from fastapi import APIRouter, Depends, HTTPException

from backend.audit.service import registrar_evento
from backend.auth.dependencies import get_current_user, get_current_user_allow_password_change
from backend.auth.permissions import require_role
from backend.auth.service import login_user
from backend.db import connect, query
from backend.users.password_reset_service import limpar_tokens_reset_expirados_ou_usados
from backend.users.schemas import ChangePasswordIn
from backend.users.service import alterar_senha, resetar_senha_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def listar_usuarios(user=Depends(get_current_user)):
    require_role("admin")(user)
    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT id, username, role, created_at
              FROM users
             ORDER BY username
            """,
            {},
        )
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.get("/users/{username}/check")
def check_user(username: str, user=Depends(get_current_user)):
    return {
        "username": user.username,
        "role": user.role,
        "must_change_password": bool(user.must_change_password),
        "password_expiring_soon": bool(user.password_expiring_soon),
        "password_days_remaining": int(user.password_days_remaining),
    }


@router.post("/users/{username}/reset-password")
def reset_password(username: str, user=Depends(get_current_user)):
    require_role("admin")(user)
    nova_senha = resetar_senha_admin(username, user)

    return {
        "username": username,
        "temporary_password": nova_senha,
        "warning": "Copie a senha agora. Ela não será exibida novamente.",
    }


@router.post("/password-reset/cleanup")
def cleanup_password_reset_tokens(user=Depends(get_current_user)):
    require_role("admin")(user)
    deleted = limpar_tokens_reset_expirados_ou_usados()
    return {
        "deleted_tokens": deleted,
        "message": "Tokens expirados/usados removidos com sucesso",
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn, user=Depends(get_current_user_allow_password_change)
):
    try:
        alterar_senha(
            username=user.username,
            senha_atual=payload.old_password,
            nova_senha=payload.new_password,
        )

        # # 🔐 cria nova sessão (zera contexto antigo)
        # access_token, refresh_token = login_user(
        #     user.username,
        #     user.role,
        # )

        registrar_evento(
            username=user.username,
            role=user.role,
            action="CHANGE_PASSWORD",
            resource="users",
            resource_id=None,
            payload_before=None,
            payload_after=None,
            endpoint="/change-password",
            method="POST",
        )

        return {"message": "Senha alterada com sucesso"}
        # return {
        #     "access_token": access_token,
        #     "refresh_token": refresh_token,
        #     "user": {
        #         "username": user.username,
        #         "role": user.role,
        #     },
        # }

    except HTTPException as exc:
        # ⚠️ Erros de negócio esperados (senha inválida, política, etc)
        raise exc
    except Exception:
        # 🔥 Erros inesperados
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao alterar senha",
        )
