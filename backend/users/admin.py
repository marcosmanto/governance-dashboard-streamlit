from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.audit.anchor import perform_anchoring
from backend.audit.service import registrar_evento
from backend.auth.dependencies import get_current_user, get_current_user_allow_password_change
from backend.auth.permissions import require_role
from backend.auth.service import revoke_all_sessions
from backend.db import connect, execute, query
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


@router.put("/users/{username}/email")
def update_user_email(
    username: str,
    payload: dict,
    admin=Depends(get_current_user),
):
    require_role("admin")(admin)

    new_email = payload.get("email")
    if not new_email:
        raise HTTPException(status_code=400, detail="Email obrigatório")

    conn = connect()
    try:
        # valida se já existe
        existing_user = query(
            conn,
            """
            SELECT 1
              FROM users
             WHERE username != :username
               AND email = :email
            """,
            {"username": username, "email": new_email},
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="EMAIL_ALREADY_IN_USE")

        execute(
            conn,
            """
            UPDATE users
               SET email = :email
             WHERE username = :username
            """,
            {"username": username, "email": new_email},
        )

        conn.commit()

        return {"message": "Email atualizado com sucesso"}
    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        conn.close()


@router.get("/audit/evidence")
def get_audit_evidence(user=Depends(get_current_user)):
    """
    Retorna o relatório forense da última violação detectada.
    """
    require_role("admin")(user)
    conn = connect()
    try:
        # Busca status de integridade
        integrity = query(conn, "SELECT * FROM audit_integrity WHERE id=1")[0]

        evidence = dict(integrity)

        # Se houver violação, busca o evento de violação registrado
        if integrity["status"] == "VIOLATED":
            violation_event = query(
                conn,
                "SELECT * FROM auditoria WHERE action='AUDIT_VIOLATION' ORDER BY id DESC LIMIT 1",
            )
            if violation_event:
                evidence["forensic_record"] = dict(violation_event[0])

        return evidence
    finally:
        conn.close()


@router.post("/audit/anchor")
def create_anchor(user=Depends(get_current_user)):
    """
    Gera âncoras criptográficas de auditoria (Local, Git e Pastebin se configurado).
    """
    require_role("admin")(user)
    results = perform_anchoring(user)
    return {"message": "Âncora criada com sucesso", "details": results}


@router.get("/role-requests")
def list_role_requests(user=Depends(get_current_user)):
    require_role("admin")(user)
    conn = connect()
    try:
        return [
            dict(row) for row in query(conn, "SELECT * FROM role_requests ORDER BY created_at DESC")
        ]
    finally:
        conn.close()


@router.post("/role-requests/{req_id}/{action}")
def process_role_request(req_id: int, action: str, user=Depends(get_current_user)):
    require_role("admin")(user)
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Ação inválida")

    conn = connect()
    try:
        req = query(conn, "SELECT * FROM role_requests WHERE id = :id", {"id": req_id})
        if not req:
            raise HTTPException(404, "Solicitação não encontrada")
        req = req[0]

        if req["status"] != "PENDING":
            raise HTTPException(400, "Solicitação já processada")

        new_status = "APPROVED" if action == "approve" else "REJECTED"
        now = datetime.now(timezone.utc).isoformat()

        # Atualiza status do pedido
        execute(
            conn,
            """
            UPDATE role_requests
               SET status = :s, processed_at = :t, processed_by = :by
             WHERE id = :id
            """,
            {"s": new_status, "t": now, "by": user.username, "id": req_id},
        )

        if action == "approve":
            # 1. Atualiza Role do Usuário
            execute(
                conn,
                "UPDATE users SET role = :r WHERE username = :u",
                {"r": req["requested_role"], "u": req["username"]},
            )
            # 2. Revoga sessões (força re-login para pegar novo role)
            revoke_all_sessions(req["username"], conn=conn)

        # Auditoria
        registrar_evento(
            conn=conn,
            username=user.username,
            role=user.role,
            action=f"ROLE_REQUEST_{new_status}",
            resource="users",
            resource_id=req_id,
            payload_before={"role": "old_role_unknown", "request_status": "PENDING"},
            payload_after={
                "target_user": req["username"],
                "new_role": req["requested_role"] if action == "approve" else None,
                "status": new_status,
            },
            endpoint=f"/admin/role-requests/{req_id}/{action}",
            method="POST",
        )

        conn.commit()
        return {"message": f"Solicitação {new_status}"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
