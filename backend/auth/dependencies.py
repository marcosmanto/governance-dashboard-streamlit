from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.core.config import settings
from backend.db import connect, query
from backend.models import UserContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        session_id = payload.get("sid")
        username = payload.get("sub")
        role = payload.get("role")

        if not session_id or not username or not role:
            raise HTTPException(status_code=401, detail="Token inválido")

        conn = connect()

        try:
            rows = query(
                conn,
                """
                SELECT revoked, expires_at
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

        if datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401)

        # return {"username": username, "role": role, "session_id": session_id}
        return UserContext(
            username=username,
            role=role,
            session_id=session_id,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Erro ao decodificar o token")
