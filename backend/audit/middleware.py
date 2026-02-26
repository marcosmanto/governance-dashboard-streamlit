import json
from typing import Optional

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.models import UserContext


class HeaderInjectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 🔐 Se usuário autenticado foi resolvido pela dependency
        user: Optional[UserContext] = getattr(request.state, "user", None)

        if user:
            response.headers["X-User-Context"] = json.dumps(
                {
                    "username": user.username,
                    "role": user.role,
                    "session_id": user.session_id,
                    "must_change_password": user.must_change_password,
                    "password_expiring_soon": user.password_expiring_soon,
                    "password_days_remaining": user.password_days_remaining,
                }
            )

        return response
