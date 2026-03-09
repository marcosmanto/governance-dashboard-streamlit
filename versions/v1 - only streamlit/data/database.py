import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "dados.db"


def criar_conexao():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
