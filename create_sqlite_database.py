import sqlite3
from pathlib import Path

db_path = Path.cwd() / "painel_dados_chatgpt_tutorial" / "data" / "dados.db"
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    categoria TEXT NOT NULL,
    valor INTEGER NOT NULL
)
""")

dados = [
    ("2025-01-01", "A", 10),
    ("2025-01-02", "A", 15),
    ("2025-01-03", "B", 8),
    ("2025-01-04", "B", 20),
    ("2025-01-05", "A", 7),
]

cursor.execute("DELETE FROM registros")
cursor.executemany(
    "INSERT INTO registros (data, categoria, valor) VALUES (?, ?, ?)", dados
)

conn.commit()
conn.close()

print("Banco criado com sucesso.")
