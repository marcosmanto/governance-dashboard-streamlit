import re
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from backend.audit.service import registrar_evento
from backend.auth.passwords import hash_password, verify_password
from backend.auth.service import revoke_all_sessions
from backend.core.config import settings
from backend.db import connect, execute, query
from backend.models import UserContext


def authenticate_user(username: str, password: str):
    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT username, password_hash, role, is_active, must_change_password, password_expires_at, mfa_secret, mfa_enabled, email, name, fullname, avatar_path
              FROM users
             WHERE username = :username
            """,
            {"username": username},
        )
    finally:
        conn.close()

    if not rows:
        return None

    user = rows[0]

    if not user["is_active"]:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    expiring_soon = False
    days_remaining = None

    password_expires_at = user["password_expires_at"]
    if password_expires_at:
        password_expires_datetime = datetime.fromisoformat(password_expires_at)
        time_until_expiration = password_expires_datetime - datetime.now(timezone.utc)

        days_remaining = time_until_expiration.days

        if days_remaining <= settings.PASSWORD_EXPIRATION_WARNING_DAYS:
            expiring_soon = True

    return {
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
        "name": user["name"],
        "fullname": user["fullname"],
        "avatar_path": user["avatar_path"],
        "must_change_password": bool(user["must_change_password"]),
        "password_expiring_soon": expiring_soon,
        "password_days_remaining": days_remaining,
        "mfa_secret": user["mfa_secret"],
        "mfa_enabled": bool(user["mfa_enabled"]),
    }


def validar_senha(password: str):
    if len(password) < 6:
        raise ValueError("Senha deve ter no mínimo 6 caracteres")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Senha deve conter letra maiúscula")

    if not re.search(r"[a-z]", password):
        raise ValueError("Senha deve conter letra minúscula")

    if not re.search(r"\d", password):
        raise ValueError("Senha deve conter número")

    if not re.search(r"[^\w\s]", password):
        raise ValueError("Senha deve conter caractere especial")


def gerar_senha_temporaria(tamanho: int = 6) -> str:
    minusculas = string.ascii_lowercase
    maiusculas = string.ascii_uppercase
    numeros = string.digits
    caracteres_especiais = string.punctuation

    # 1️⃣ garante 1 de cada
    senha = [
        secrets.choice(minusculas),
        secrets.choice(maiusculas),
        secrets.choice(numeros),
        secrets.choice(caracteres_especiais),
    ]

    # 2️⃣ completa o resto
    todos = minusculas + maiusculas + numeros + caracteres_especiais
    senha += [secrets.choice(todos) for _ in range(2)]

    # 3️⃣ embaralha
    secrets.SystemRandom().shuffle(senha)
    return "".join(senha)


def resetar_senha_admin(username: str, admin_user: UserContext):
    # gera senha temporária
    nova_senha = gerar_senha_temporaria()

    # valida senha temporária
    validar_senha(nova_senha)

    conn = connect()
    try:
        # 🔐 Atualiza senha
        execute(
            conn,
            """
            UPDATE users
               SET password_hash = :hash,
                   must_change_password = 1
             WHERE username = :username
            """,
            {
                "hash": hash_password(nova_senha),
                "username": username,
            },
        )

        revoke_all_sessions(username, conn=conn)

        # 🧾 Auditoria (MESMA conexão)
        registrar_evento(
            conn=conn,
            username=admin_user.username,
            role=admin_user.role,
            action="RESET_PASSWORD_ADMIN",
            resource="users/admin",
            resource_id=None,
            payload_before={"username": username},
            payload_after=None,
            endpoint="/admin/users/reset-password",
            method="POST",
        )

        conn.commit()
        return nova_senha
    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        conn.close()


def alterar_senha(*, username: str, senha_atual: str, nova_senha: str):
    try:
        validar_senha(nova_senha)
    except ValueError as exc:
        # ❌ Política de senha
        raise HTTPException(status_code=400, detail=str(exc))

    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT password_hash
              FROM users
             WHERE username = :username
            """,
            {"username": username},
        )

        if not rows:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        password_hash = rows[0]["password_hash"]

        if not verify_password(senha_atual, password_hash):
            raise HTTPException(status_code=400, detail="Senha atual inválida")

        execute(
            conn,
            """
            UPDATE users
               SET password_hash = :password_hash,
                   must_change_password = 0,
                   password_changed_at = :changed_at,
                   password_expires_at = :expires_at
             WHERE username = :username
            """,
            {
                "password_hash": hash_password(nova_senha),
                "username": username,
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(days=settings.PASSWORD_VALIDITY_DAYS)
                ).isoformat(),
            },
        )

        revoke_all_sessions(username, conn=conn)

        conn.commit()
    finally:
        conn.close()


def resetar_senha_por_token(*, username: str, nova_senha: str):
    """
    Reseta a senha sem exigir a senha atual (uso com token válido).
    """
    try:
        validar_senha(nova_senha)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT password_hash
              FROM users
             WHERE username = :username
               AND is_active = 1
            """,
            {"username": username},
        )

        if not rows:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        execute(
            conn,
            """
            UPDATE users
               SET password_hash = :password_hash,
                   must_change_password = 0,
                   password_changed_at = :changed_at,
                   password_expires_at = :expires_at
             WHERE username = :username
            """,
            {
                "password_hash": hash_password(nova_senha),
                "username": username,
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(days=settings.PASSWORD_VALIDITY_DAYS)
                ).isoformat(),
            },
        )

        conn.commit()
    finally:
        conn.close()
