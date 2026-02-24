import uuid
from datetime import datetime, timezone

from backend.core.logger import logger
from fastapi import HTTPException

from backend.auth.jwt import create_token
from backend.core.config import ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE, settings
from backend.db import connect, execute, query


def login_user(username: str, role: str):
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    conn = connect()
    try:
        # 1️⃣ Buscar versão da senha
        rows = query(
            conn,
            """
            SELECT password_changed_at, password_expires_at
            FROM users
            WHERE username = :username
            """,
            {"username": username},
        )

        if not rows:
            raise HTTPException(status_code=401, detail="Usuário inválido")

        if rows[0]["password_expires_at"]:
            expires_at = datetime.fromisoformat(rows[0]["password_expires_at"])
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=403, detail="PASSWORD_EXPIRED")

        password_changed_at = rows[0]["password_changed_at"]

        # 2️⃣ Criar sessão
        execute(
            conn,
            """
            INSERT INTO user_sessions
            (id, username, role, created_at, expires_at)
            VALUES (:id, :username, :role, :created_at, :expires_at)
            """,
            {
                "id": session_id,
                "username": username,
                "role": role,
                "created_at": now.isoformat(),
                "expires_at": (now + REFRESH_TOKEN_EXPIRE).isoformat(),
            },
        )
        conn.commit()
    finally:
        conn.close()

    # 3️⃣ Criar tokens
    access_token = create_token(
        {
            "sub": username,
            "role": role,
            "sid": session_id,
            "pwd": password_changed_at,  # 🔑 versão da senha
        },
        ACCESS_TOKEN_EXPIRE,
    )

    refresh_token = create_token(
        {
            "sub": username,
            "sid": session_id,
            "type": "refresh",
            "pwd": password_changed_at,
        },
        REFRESH_TOKEN_EXPIRE,
    )

    return access_token, refresh_token


def logout_session(session_id: str):
    conn = connect()
    try:
        execute(
            conn,
            """
            UPDATE user_sessions
               SET revoked = 1
             WHERE id = :id
            """,
            {"id": session_id},
        )
        conn.commit()
    finally:
        conn.close()


def issue_new_access_token(payload: dict) -> dict:
    session_id = payload.get("sid")
    username = payload.get("sub")
    pwd_token = payload.get("pwd")

    if not session_id or not username or not pwd_token:
        raise HTTPException(status_code=401, detail="Token inválido")

    conn = connect()
    try:
        now = datetime.now(timezone.utc)

        # 1️⃣ Validar sessão atual
        session_rows = query(
            conn,
            """
            SELECT revoked, expires_at, role
              FROM user_sessions
             WHERE id = :id
            """,
            {"id": session_id},
        )

        if not session_rows:
            raise HTTPException(status_code=401)

        session = session_rows[0]

        if session["revoked"]:
            raise HTTPException(status_code=401)

        # expires_at = datetime.fromisoformat(session["expires_at"])
        # if expires_at < now:
        #     raise HTTPException(status_code=401)

        # 2️⃣ Buscar versão atual da senha
        user_rows = query(
            conn,
            """
            SELECT password_changed_at
            FROM users
            WHERE username = :username
            """,
            {"username": username},
        )

        if not user_rows:
            raise HTTPException(status_code=401, detail="Usuário inválido")

        pwd_db = user_rows[0]["password_changed_at"]

        # 3️⃣ Comparar versões
        if pwd_token != pwd_db:
            raise HTTPException(status_code=401, detail="PASSWORD_CHANGE")

        # 🔁 4️⃣ ROTACIONAR SESSÃO
        # 4.1 Revogar sessão atual
        execute(
            conn,
            """
            UPDATE user_sessions
               SET revoked = 1
             WHERE id = :id
            """,
            {"id": session_id},
        )

        # 4.2 Criar nova sessão
        new_session_id = str(uuid.uuid4())
        new_expires_at = now + REFRESH_TOKEN_EXPIRE
        execute(
            conn,
            """
            INSERT INTO user_sessions
                (id, username, role, created_at, expires_at, revoked)
            VALUES
                (:id, :username, :role, :created_at, :expires_at, 0)
            """,
            {
                "id": new_session_id,
                "username": username,
                "role": session["role"],
                "created_at": now.isoformat(),
                "expires_at": new_expires_at.isoformat(),
            },
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        # ⚠️ Apenas em desenvolvimento, retorna o token no response
        if settings.ENV == "dev":
            logger.warning(f"Erro ao tentar REFRESH da sessão do usuário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao tentar REFRESH da sessão do usuário")
    finally:
        conn.close()

    # 🔐 5️⃣ Emitir NOVOS tokens com novo sid
    new_access_token = create_token(
        {
            "sub": username,
            "role": session["role"],
            "sid": new_session_id,
            "pwd": pwd_db,  # 🔑 sempre a versão atual
        },
        ACCESS_TOKEN_EXPIRE,
    )

    new_refresh_token = create_token(
        {
            "sub": username,
            "sid": new_session_id,
            "type": "refresh",
            "pwd": pwd_db,  # 🔐 importante para manter coerência
        },
        REFRESH_TOKEN_EXPIRE,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }


def revoke_all_sessions(username: str, conn=None):
    """
    Revoga todas as sessões ativas de um usuário.
    """

    if not username:
        raise HTTPException(status_code=400, detail="Username obrigatório")

    ows_connection = False
    if conn is None:
        ows_connection = True
        conn = connect()

    try:
        execute(
            conn,
            """
            UPDATE user_sessions
               SET revoked = 1
             WHERE username = :username
               AND revoked = 0
            """,
            {"username": username},
        )

        if ows_connection:
            conn.commit()
    except Exception:
        if ows_connection:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Erro ao revogar sessões do usuário")
    finally:
        if ows_connection:
            conn.close()


def revoke_session_by_id(session_id: str):
    conn = connect()
    try:
        execute(
            conn,
            """
            UPDATE user_sessions
               SET revoked = 1
             WHERE id = :id
            """,
            {"id": session_id},
        )
        conn.commit()
    finally:
        conn.close()


def cleanup_expired_sessions() -> int:
    conn = connect()
    try:
        cur = execute(
            conn,
            """
            DELETE FROM user_sessions
             WHERE expires_at < :now
            """,
            {"now": datetime.now(timezone.utc).isoformat()},
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def cleanup_revoked_sessions() -> int:
    conn = connect()
    try:
        cur = execute(
            conn,
            """
            DELETE FROM user_sessions
             WHERE revoked = 1
            """,
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
