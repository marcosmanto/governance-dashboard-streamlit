import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "dados.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
