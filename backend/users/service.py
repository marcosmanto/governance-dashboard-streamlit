from backend.auth.passwords import verify_password
from backend.db import connect, query


def authenticate_user(username: str, password: str):
    conn = connect()
    try:
        rows = query(
            conn,
            """
            SELECT username, password_hash, role, is_active
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
    }
