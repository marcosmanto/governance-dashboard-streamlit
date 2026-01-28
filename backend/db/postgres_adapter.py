# backend/db/postgres_adapter.py
from __future__ import annotations

from typing import Any, Dict

from .errors import DBError, DuplicateKeyError, ForeignKeyError

try:
    import psycopg  # psycopg3
except Exception:  # pragma: no cover
    psycopg = None


def connect(dsn: str | None = None):
    if psycopg is None:
        raise RuntimeError("psycopg não instalado. pip install psycopg[binary]")
    return psycopg.connect(dsn)


def execute(conn, sql: str, params: Dict[str, Any] | None = None):
    # Em psycopg, placeholder é %s; se você mantiver :nome,
    # pode usar psycopg.sql ou mapear para %s + tupla.
    # Para simplificar, psycopg aceita dict com %(nome)s se você formatar.
    # Implementar conversão aqui quando for migrar de fato.
    cur = conn.cursor()
    cur.execute(sql, params or None)
    return cur


def executemany(conn, sql: str, seq_of_params):
    cur = conn.cursor()
    cur.executemany(sql, seq_of_params)
    return cur


def query(conn, sql: str, params: Dict[str, Any] | None = None):
    cur = execute(conn, sql, params)
    return cur.fetchall()


def normalize_error(exc: Exception) -> DBError:
    # from psycopg import errors
    try:
        from psycopg import errors

        if isinstance(exc, errors.UniqueViolation):
            return DuplicateKeyError(str(exc))
        if isinstance(exc, errors.ForeignKeyViolation):
            return ForeignKeyError(str(exc))
    except Exception:
        pass
    return DBError(str(exc))
