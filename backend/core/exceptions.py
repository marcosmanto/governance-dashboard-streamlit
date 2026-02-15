from logging import Logger

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings


def register_exception_handlers(app: FastAPI, logger: Logger):
    @app.exception_handler(FastAPIHTTPException)
    async def custom_http_exception_handler(request: Request, exc: FastAPIHTTPException):
        # 🔎 Apenas em ambiente de desenvolvimento
        if settings.ENV == "dev" and exc.status_code == 401:
            logger.warning(f"401 em {request.method} {request.url.path} - detail={exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


def register_rate_limit_exception(app: FastAPI):
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "RATE_LIMIT_EXCEEDED"},
        )
