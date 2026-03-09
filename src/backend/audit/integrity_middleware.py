from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.audit.guard import is_system_locked


class IntegrityGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 🔓 Permitir autenticação mesmo em bloqueio (para o admin entrar e corrigir)
        if request.url.path in ["/login", "/refresh", "/logout"]:
            return await call_next(request)

        # Se for operação de escrita (POST, PUT, DELETE, PATCH)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if is_system_locked():
                return JSONResponse(
                    status_code=status.HTTP_423_LOCKED,
                    content={
                        "detail": "SISTEMA BLOQUEADO: Violação de integridade detectada na auditoria."
                    },
                )
        return await call_next(request)
