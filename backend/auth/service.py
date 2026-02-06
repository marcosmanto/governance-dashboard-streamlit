import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from backend.auth.jwt import create_token
from backend.core.config import ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE
from backend.db import connect, execute, query


def login_user(username: str, role: str):
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    conn = connect()
    try:
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

    access_token = create_token(
        {"sub": username, "role": role, "sid": session_id},
        ACCESS_TOKEN_EXPIRE,
    )

    refresh_token = create_token(
        {"sub": username, "sid": session_id, "type": "refresh"},
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


def issue_new_access_token(payload: dict) -> str:
    session_id = payload.get("sid")
    username = payload.get("sub")

    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT revoked, expires_at, role
              FROM user_sessions
             WHERE id = :id
            """,
            {"id": session_id},
        )
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=401)

    session = rows[0]
    if session["revoked"]:
        raise HTTPException(status_code=401)

    access_token = create_token(
        {"sub": username, "role": session["role"], "sid": session_id},
        ACCESS_TOKEN_EXPIRE,
    )

    return access_token


def revoke_all_sessions(username: str):
    """
    Revoga todas as sessões ativas de um usuário.
    """
    if not username:
        raise HTTPException(status_code=400, detail="Username obrigatório")

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
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Erro ao revogar sessões do usuário")
    finally:
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
