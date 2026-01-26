"""
V003 — Unicidade por (data, categoria), upsert via view e WAL mode.

Passos:
1) Remove duplicados preservando o mais recente por (data, categoria).
2) Cria índice ÚNICO em (data, categoria) e índice auxiliar (categoria, data).
3) Cria view + gatilho INSTEAD OF INSERT para upsert.
4) Ativa WAL mode e synchronous=NORMAL (fora de transação).
"""


def upgrade(conn):
    # 1) Remoção idempotente de duplicados por (data, categoria)
    conn.executescript(
        """
        WITH ranked AS (
            SELECT
                id,
                data,
                categoria,
                ROW_NUMBER() OVER (
                    PARTITION BY data, categoria
                    ORDER BY COALESCE(atualizado_em, criado_em) DESC, id DESC
                ) AS rn
            FROM registros
        )
        DELETE FROM registros
        WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
        """
    )

    # 2) Índices (UNIQUE e auxiliar)
    conn.executescript(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_registros_data_categoria
            ON registros (data, categoria);

        CREATE INDEX IF NOT EXISTS ix_registros_categoria_data
            ON registros (categoria, data);
        """
    )

    # 3) View + gatilho de UPSERT
    conn.executescript(
        """
        DROP TRIGGER IF EXISTS trg_vw_registros_upsert_insert;
        DROP VIEW IF EXISTS vw_registros_upsert;

        CREATE VIEW IF NOT EXISTS vw_registros_upsert AS
        SELECT id, data, categoria, valor, criado_em, atualizado_em, origem
        FROM registros;

        CREATE TRIGGER trg_vw_registros_upsert_insert
        INSTEAD OF INSERT ON vw_registros_upsert
        FOR EACH ROW
        BEGIN
            INSERT INTO registros (data, categoria, valor, origem)
            VALUES (NEW.data, NEW.categoria, NEW.valor, NEW.origem)
            ON CONFLICT(data, categoria) DO UPDATE SET
                valor          = excluded.valor,
                origem         = COALESCE(excluded.origem, registros.origem),
                atualizado_em  = CURRENT_TIMESTAMP;
        END;
        """
    )

    # 4) Ativa WAL fora de transação: faz um commit explícito e aplica PRAGMAs
    conn.commit()  # encerra a transação aberta pelo runner (IMPORTANTE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
