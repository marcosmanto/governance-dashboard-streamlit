from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

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
                SELECT
                    s.revoked,
                    s.expires_at,
                    u.must_change_password
                  FROM user_sessions s
                  JOIN users u ON u.username = s.username
                 WHERE s.id = :id
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

        if rows[0]["must_change_password"]:
            raise HTTPException(status_code=403, detail="PASSWORD_CHANGE_REQUIRED")

        # return {"username": username, "role": role, "session_id": session_id}
        return UserContext(
            username=username,
            role=role,
            session_id=session_id,
            must_change_password=bool(rows[0]["must_change_password"]),
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Erro ao decodificar o token")


def get_current_user_allow_password_change(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        # 🔑 Access token expirou → frontend tentará refresh
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN",
        )

    return UserContext(
        username=payload.get("sub"),
        role=payload.get("role"),
        session_id=payload.get("sid"),
        must_change_password=True,
    )
