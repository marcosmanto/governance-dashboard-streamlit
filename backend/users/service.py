import re
import secrets
import string

from fastapi import HTTPException

from backend.audit.service import registrar_evento
from backend.auth.passwords import hash_password, verify_password
from backend.db import connect, execute, query
from backend.models import UserContext


def authenticate_user(username: str, password: str):
    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT username, password_hash, role, is_active, must_change_password
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

    return {
        "username": user["username"],
        "role": user["role"],
        "must_change_password": bool(user["must_change_password"]),
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

        # 🧾 Auditoria (MESMA conexão)
        registrar_evento(
            conn=conn,
            username=admin_user.username,
            role=admin_user.role,
            action="RESET_PASSWORD",
            resource="users",
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
                   must_change_password = 0
             WHERE username = :username
            """,
            {
                "password_hash": hash_password(nova_senha),
                "username": username,
            },
        )

        conn.commit()
    finally:
        conn.close()
