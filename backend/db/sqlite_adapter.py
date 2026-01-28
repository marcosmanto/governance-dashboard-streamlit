from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple

from .errors import DBError, DuplicateKeyError, ForeignKeyError

# Caminho padrão do seu projeto: <repo>/data/dados.db
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "dados.db"


def connect(dsn: str | None = None) -> sqlite3.Connection:
    db_path = Path(dsn) if dsn else _DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # Opcional: melhor compatibilidade com dicts/tuplas
    conn.row_factory = sqlite3.Row
    return conn


# --- Placeholder conversion: from ":name" to "?" (qmark) ---
_named_re = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def _compile_sql(sql: str, params: Dict[str, Any] | None) -> Tuple[str, Sequence[Any] | None]:
    if not params:
        return sql, None
    order: list[str] = _named_re.findall(sql)  # ordem de ocorrência
    compiled_sql = _named_re.sub("?", sql)
    compiled_params = [params[name] for name in order]
    return compiled_sql, compiled_params


def execute(conn, sql: str, params: Dict[str, Any] | None = None):
    sql2, p2 = _compile_sql(sql, params)
    cur = conn.cursor()
    cur.execute(sql2, p2 or [])
    return cur


def executemany(conn, sql: str, seq_of_params: Iterable[Dict[str, Any]]):
    cur = conn.cursor()
    for p in seq_of_params:
        sql2, p2 = _compile_sql(sql, p)
        cur.execute(sql2, p2 or [])
    return cur


def query(conn, sql: str, params: Dict[str, Any] | None = None):
    cur = execute(conn, sql, params)
    return cur.fetchall()


def normalize_error(exc: Exception) -> DBError:
    # sqlite3.IntegrityError cobre UNIQUE, FK etc.
    if isinstance(exc, sqlite3.IntegrityError):
        msg = str(exc).lower()
        if "unique" in msg:
            return DuplicateKeyError(str(exc))
        if "foreign key" in msg:
            return ForeignKeyError(str(exc))
    return DBError(str(exc))
