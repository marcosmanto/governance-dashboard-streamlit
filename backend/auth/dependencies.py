from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

from backend.core.config import settings
from backend.db import connect, query
from backend.models import UserContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
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
                    u.must_change_password,
                    u.password_expires_at
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

        # Sessão revogada
        if session["revoked"]:
            raise HTTPException(status_code=401)

        # Access token expirou
        if datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401)

        # 🔐 Expiração automática da senha (senha expirada por idade)
        expiring_soon = False
        days_remaining = None

        password_expires_at = session["password_expires_at"]
        if password_expires_at:
            password_expires_datetime = datetime.fromisoformat(password_expires_at)
            time_until_expiration = password_expires_datetime - datetime.now(timezone.utc)

            if time_until_expiration.total_seconds() <= 0:
                raise HTTPException(status_code=403, detail="PASSWORD_EXPIRED")

            days_remaining = time_until_expiration.days

            expiring_soon = days_remaining <= settings.PASSWORD_EXPIRATION_WARNING_DAYS

        # must_change_password = 1
        if session["must_change_password"]:
            raise HTTPException(status_code=403, detail="PASSWORD_CHANGE_REQUIRED")

        # return {"username": username, "role": role, "session_id": session_id}
        user_context = UserContext(
            username=username,
            role=role,
            session_id=session_id,
            must_change_password=bool(session["must_change_password"]),
            password_expiring_soon=expiring_soon,
            password_days_remaining=days_remaining,
        )

        request.state.user = user_context
        return user_context

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
