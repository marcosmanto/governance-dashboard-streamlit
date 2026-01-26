#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class MigrationFile:
    version: int
    name: str
    path: Path
    kind: str  # 'sql' or 'py'
    checksum: str


def compute_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def discover_migrations(migrations_dir: Path) -> List[MigrationFile]:
    files: List[MigrationFile] = []
    for p in sorted(migrations_dir.glob("V*__*.*")):
        if p.suffix.lower() not in (".sql", ".py"):
            continue
        stem = p.stem  # ex: V001__create_registros
        try:
            vpart, name = stem.split("__", 1)
            version = int(vpart[1:])  # remove 'V'
        except Exception:
            print(f"Ignorando arquivo com nome inválido: {p.name}", file=sys.stderr)
            continue

        kind = p.suffix.lower().lstrip(".")
        checksum = compute_checksum(p.read_bytes())
        files.append(
            MigrationFile(
                version=version, name=name, path=p, kind=kind, checksum=checksum
            )
        )
    return sorted(files, key=lambda m: m.version)


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """
    )


def get_applied(conn: sqlite3.Connection) -> Dict[int, Tuple[str, str]]:
    # retorna {version: (name, checksum)}
    rows = conn.execute(
        "SELECT version, name, checksum FROM schema_migrations"
    ).fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


def backup_db_online(db_path: Path) -> Path:
    """
    Usa a API de backup do SQLite (conn.backup) — funciona mesmo com o banco aberto,
    evitando problemas de bloqueio no Windows.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.bak_{timestamp}{db_path.suffix}")
    src = sqlite3.connect(str(db_path))
    try:
        dst = sqlite3.connect(str(backup_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    print(f"[backup] {backup_path}")
    return backup_path


def apply_sql(conn: sqlite3.Connection, sql_text: str) -> None:
    conn.executescript(sql_text)


def apply_py(conn: sqlite3.Connection, file_path: Path) -> None:
    # módulo com função obrigatória upgrade(conn)
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    if not hasattr(module, "upgrade"):
        raise RuntimeError(f"{file_path.name}: faltou função upgrade(conn).")
    module.upgrade(conn)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runner simples de migrações para SQLite (SQL e Python).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--db", required=True, help="Caminho do arquivo .db")
    parser.add_argument(
        "--migrations", default="./migrations", help="Pasta das migrações"
    )
    parser.add_argument(
        "--target-version", type=int, help="Versão-alvo (aplica até esta versão)"
    )
    parser.add_argument("--list", action="store_true", help="Lista migrações e sai")
    parser.add_argument(
        "--dry-run", action="store_true", help="Mostra o que faria, sem aplicar"
    )
    parser.add_argument(
        "--fake",
        action="store_true",
        help="Marca como aplicado sem executar (use com cuidado)",
    )
    parser.add_argument(
        "--init-if-missing",
        action="store_true",
        help="Cria o arquivo do banco (e pastas) se não existir, antes de aplicar as migrações",
    )

    args = parser.parse_args()

    db_path = Path(args.db)
    mig_dir = Path(args.migrations)

    if not db_path.exists():
        if args.init_if_missing:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # cria um DB vazio
            sqlite3.connect(str(db_path)).close()
            print(f"Banco de dados criado: {db_path}")
        else:
            print(f"ERRO: Banco de dados não encontrado: {db_path}", file=sys.stderr)
            sys.exit(1)

    if not mig_dir.exists():
        print(f"ERRO: Pasta de migrações não encontrada: {mig_dir}", file=sys.stderr)
        sys.exit(1)

    migrations = discover_migrations(mig_dir)
    if args.list:
        print("Migrações encontradas:")
        for m in migrations:
            print(f"  V{m.version:03d}  {m.name}  ({m.kind})  {m.path.name}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    try:
        ensure_migrations_table(conn)
        applied = get_applied(conn)

        to_apply: List[MigrationFile] = []
        for m in migrations:
            if args.target_version is not None and m.version > args.target_version:
                break
            if m.version in applied:
                # Verifica divergência de checksum (arquivo mudou após aplicado)
                _, old_checksum = applied[m.version]
                if old_checksum != m.checksum:
                    print(
                        f"⚠️ Divergência: V{m.version:03d} '{m.name}' já aplicado, "
                        f"mas o arquivo atual mudou (checksum diferente).",
                        file=sys.stderr,
                    )
                continue
            to_apply.append(m)

        if not to_apply:
            print("Nada a aplicar. ✅")
            return

        print("Plano de aplicação:")
        for m in to_apply:
            print(f"  V{m.version:03d}  {m.name}  ({m.kind})")

        if args.dry_run:
            print("\n-- DRY RUN: nenhuma alteração foi feita.")
            return

        backup_db_online(db_path)

        for m in to_apply:
            print(f"Aplicando V{m.version:03d} {m.name} ({m.kind}) ...")
            with conn:  # transação
                if not args.fake:
                    if m.kind == "sql":
                        apply_sql(conn, m.path.read_text(encoding="utf-8"))
                    else:
                        apply_py(conn, m.path)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?)",
                    (m.version, m.name, m.checksum),
                )
        print("✅ Todas as migrações necessárias foram aplicadas com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
