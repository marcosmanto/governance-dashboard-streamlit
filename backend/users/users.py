import logging

from fastapi import APIRouter, HTTPException

from backend.audit.service import registrar_evento
from backend.auth.service import revoke_all_sessions
from backend.core.config import settings
from backend.db import connect, query
from backend.users.models import ForgotPasswordIn, ResetPasswordIn
from backend.users.password_reset_service import (
    gerar_token_reset_senha,
    marcar_token_como_usado,
    validar_token_reset_senha,
)
from backend.users.service import resetar_senha_por_token

router = APIRouter(tags=["Users"])
logger = logging.getLogger("uvicorn.error")


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn):
    """
    Gera token de reset de senha.
    Em produção, o token deve ser enviado por e-mail.
    """
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username obrigatório")

    try:
        logger.info("Forgot-password solicitado")
        conn = connect()
        try:
            rows = query(
                conn,
                """
                SELECT 1
                  FROM users
                 WHERE username = :username
                   AND is_active = 1
                """,
                {"username": username},
            )
        finally:
            conn.close()

        token = None
        if rows:
            logger.info("Usuário ativo encontrado para reset de senha")
            token = gerar_token_reset_senha(username=username)
        else:
            logger.info("Usuário não encontrado ou inativo para reset de senha")

        registrar_evento(
            username=username,
            role="system",
            action="FORGOT_PASSWORD",
            resource="users",
            resource_id=None,
            payload_before=None,
            payload_after=None,
            endpoint="/forgot-password",
            method="POST",
        )

        # 200 genérico para não revelar se o usuário existe
        response = {
            "message": "Se o usuário existir, você receberá instruções para redefinir a senha."
        }

        # ⚠️ Apenas em desenvolvimento, retorna o token no response
        if settings.ENV == "dev" and token:
            response["reset_token"] = token
            logger.warning(f"Token de reset: {token}")

        return response

    except HTTPException:
        logger.warning("Erro de validação ao solicitar reset de senha", exc_info=True)
        raise
    except Exception:
        logger.exception("Erro inesperado no fluxo de forgot-password")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao solicitar redefinição de senha",
        )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn):
    """
    Reseta senha usando token.
    """
    try:
        logger.info("Reset-password solicitado")
        # 1) valida token
        username = validar_token_reset_senha(token=payload.token)

        # 2) altera senha (aplica política)
        resetar_senha_por_token(username=username, nova_senha=payload.new_password)

        # 3) marca token como usado
        marcar_token_como_usado(token=payload.token)

        # 4) revoga sessões do usuário
        revoke_all_sessions(username)

        # 5) auditoria
        registrar_evento(
            username=username,
            role="system",
            action="RESET_PASSWORD",
            resource="users",
            resource_id=None,
            payload_before=None,
            payload_after=None,
            endpoint="/reset-password",
            method="POST",
        )

        return {"message": "Senha redefinida com sucesso"}

    except HTTPException:
        # Resposta genérica para evitar enumeração de tokens inválidos/usados/expirados
        logger.warning("Reset-password com falha de validação", exc_info=True)
        return {"message": "Se o token for válido, a senha será redefinida."}
    except Exception:
        logger.exception("Erro inesperado no fluxo de reset-password")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao redefinir a senha",
        )
