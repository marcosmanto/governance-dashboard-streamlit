import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from backend.auth.service import revoke_all_sessions
from backend.core.config import settings
from backend.db import connect, execute, query


def gerar_token_reset_senha(*, username: str, validade_minutos: int = 30) -> str:
    """
    Gera token temporário de reset de senha.
    Retorna o token PURO (para envio por e-mail).
    """

    # token imprevísivel (URL-safe)
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=validade_minutos)

    conn = connect()
    try:
        execute(
            conn,
            """
            INSERT INTO password_reset_tokens (
                username,
                token_hash,
                created_at,
                expires_at
            )
            VALUES (
                :username,
                :token_hash,
                :created_at,
                :expires_at
            )
            """,
            {
                "username": username,
                "token_hash": token_hash,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            },
        )

        revoke_all_sessions(username, conn=conn)

        conn.commit()
    finally:
        conn.close()

    # ⚠️ SOMENTE o token puro sai daqui
    return token


def validar_token_reset_senha(*, token: str) -> str:
    """
    Valida token de reset.
    Retorna username se válido.
    """

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    now = datetime.now(timezone.utc)

    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT
              id, username, expires_at, used_at
            FROM password_reset_tokens
            WHERE token_hash = :token_hash
            """,
            {"token_hash": token_hash},
        )

        if not rows:
            raise HTTPException(status_code=400, detail="Token inválido")

        row = rows[0]

        if row["used_at"] is not None:
            raise HTTPException(status_code=400, detail="Token já utilizado")

        if now > datetime.fromisoformat(row["expires_at"]):
            raise HTTPException(status_code=400, detail="Token expirado")

        return row["username"]
    finally:
        conn.close()


def assinar_token_reset(token: str) -> str:
    """
    Assina o token com HMAC usando JWT_SECRET.
    Retorna token + assinatura concatenados.
    """
    signature = hmac.new(
        settings.JWT_SECRET.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{token}.{signature}"


def validar_assinatura_token(token_assinado: str) -> str:
    """
    Separa token e assinatura.
    Valida integridade.
    Retorna token puro se válido.
    """
    try:
        token, signature = token_assinado.split(".")
    except ValueError:
        raise HTTPException(status_code=400, detail="Token inválido")

    expected_signature = hmac.new(
        settings.JWT_SECRET.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=400, detail="Token inválido")

    return token


def marcar_token_como_usado(*, token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    conn = connect()
    try:
        execute(
            conn,
            """
            UPDATE password_reset_tokens
               SET used_at = :used_at
             WHERE token_hash = :token_hash
            """,
            {
                "used_at": now.isoformat(),
                "token_hash": token_hash,
            },
        )
        conn.commit()
    finally:
        conn.close()


def limpar_tokens_reset_expirados_ou_usados() -> int:
    """
    Remove tokens expirados ou já utilizados.
    Retorna a quantidade removida.
    """
    conn = connect()
    try:
        cur = execute(
            conn,
            """
            DELETE FROM password_reset_tokens
             WHERE used_at IS NOT NULL
                OR expires_at <= CURRENT_TIMESTAMP
            """,
            {},
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
