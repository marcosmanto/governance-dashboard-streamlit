def upgrade(conn):
    """
    Cria a tabela 'registros' se não existir e insere um seed inicial de forma idempotente.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor INTEGER NOT NULL
        )
        """
    )

    # Seed idempotente: só insere se a tabela estiver vazia
    cur = conn.execute("SELECT COUNT(*) FROM registros")
    (count,) = cur.fetchone()
    if count == 0:
        dados = [
            ("2025-01-01", "A", 10),
            ("2025-01-02", "A", 15),
            ("2025-01-03", "B", 8),
            ("2025-01-04", "B", 20),
            ("2025-01-05", "A", 7),
        ]
        conn.executemany(
            "INSERT INTO registros (data, categoria, valor) VALUES (?, ?, ?)", dados
        )
