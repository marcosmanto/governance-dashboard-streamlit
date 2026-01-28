from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.audit.service import registrar_evento


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Só audita mutações bem-sucedidas
        if request.method not in ("POST", "PUT", "DELETE"):
            return response

        if response.status_code >= 400:
            return response

        # Usuário já autenticado via dependency
        user = getattr(request.state, "user", None)

        if not user:
            return response

        if request.method in ("POST", "GET"):
            registrar_evento(
                username=user.username,
                role=user.role,
                action=request.method,
                resource="registros",
                resource_id=None,  # ajustaremos nos endpoints
                payload_before=None,
                payload_after=None,
                endpoint=str(request.url.path),
                method=request.method,
            )

        return response
