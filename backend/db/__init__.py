# backend/db/__init__.py
import os

_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()
_DSN = os.getenv("DB_DSN")  # para sqlite: caminho do arquivo | para postgres: URL

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
