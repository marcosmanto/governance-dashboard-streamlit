from backend.core.config import settings

_BACKEND = settings.DB_BACKEND
_DSN = settings.DB_DSN

if _BACKEND == "sqlite":
    from . import sqlite_adapter as _adapter
else:
    from . import postgres_adapter as _adapter

connect = _adapter.connect
execute = _adapter.execute
executemany = _adapter.executemany
query = _adapter.query
normalize_error = _adapter.normalize_error


def backend_name() -> str:
    return _BACKEND


def dsn() -> str | None:
    return _DSN
