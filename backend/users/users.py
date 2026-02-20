import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.audit.service import registrar_evento
from backend.auth.dependencies import get_current_user, get_current_user_profile
from backend.auth.service import revoke_all_sessions
from backend.core.config import settings
from backend.db import connect, query
from backend.models import User, UserContext
from backend.notifications.email_service import send_email
from backend.notifications.templates import reset_password_template
from backend.users.models import ForgotPasswordIn, ResetPasswordIn
from backend.users.password_reset_service import (
    assinar_token_reset,
    gerar_token_reset_senha,
    marcar_token_como_usado,
    validar_assinatura_token,
    validar_token_reset_senha,
)
from backend.users.service import resetar_senha_por_token

router = APIRouter(tags=["Users"])
logger = logging.getLogger("auth-debug")


def _send_email_safe(to: str, subject: str, html: str):
    try:
        send_email(to, subject, html)
    except Exception as exc:
        # Em dev, é comum o email falhar se for fake. Apenas logamos o aviso.
        logger.warning(f"Falha ao enviar e-mail para {to}: {exc}")


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, background_tasks: BackgroundTasks):
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
                SELECT email
                  FROM users
                 WHERE username = :username
                   AND is_active = 1
                """,
                {"username": username},
            )
        finally:
            conn.close()

        token = None
        signed_token = None

        if rows:
            logger.info("Usuário ativo encontrado para reset de senha")

            email = rows[0]["email"]

            # 1️⃣ Gerar token puro
            token = gerar_token_reset_senha(username=username)

            # 2️⃣ Assinar token
            signed_token = assinar_token_reset(token)

            # 3️⃣ Criar link
            reset_link = f"{settings.FRONTEND_URL}?token={signed_token}"

            # 4️⃣ Criar HTML
            html_content = reset_password_template(reset_link)

            # 5️⃣ Enviar e-mail em background
            if email:
                background_tasks.add_task(
                    _send_email_safe,
                    email,
                    "Redefinição de senha",
                    html_content,
                )
            else:
                logger.warning(
                    f"Usuário {username} solicitou reset mas não possui e-mail cadastrado."
                )
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
        if settings.ENV == "dev" and signed_token:
            response["reset_token"] = signed_token
            logger.warning(f"Token de reset: {signed_token}")

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

        # 1️⃣ Validar assinatura primeiro
        token_puro = validar_assinatura_token(payload.token)

        # 2️⃣ Validar token no banco
        username = validar_token_reset_senha(token=token_puro)

        # 3️⃣ Alterar senha (aplica política)
        resetar_senha_por_token(username=username, nova_senha=payload.new_password)

        # 4️⃣ Marcar token como usado
        marcar_token_como_usado(token=token_puro)

        # 5️⃣ Revoga sessões do usuário
        revoke_all_sessions(username)

        # 6️⃣ Auditoria
        registrar_evento(
            username=username,
            role="system",
            action="RESET_PASSWORD_TOKEN",
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


@router.get("/me", response_model=User)
def get_me(user: User = Depends(get_current_user_profile)):
    return user
