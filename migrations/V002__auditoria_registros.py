"""
V002 — Camada de auditoria (compatível e idempotente).
- Garante colunas criado_em, atualizado_em, origem.
- Backfill nos valores NULL.
- (Re)cria gatilhos de auditoria.
- Cria índices se faltarem.
"""


def upgrade(conn):
    def has_column(table: str, col: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        names = {r[1] for r in rows}  # r[1] = nome da coluna
        return col in names

    def trigger_exists(name: str) -> bool:
        sql = "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?"
        return conn.execute(sql, (name,)).fetchone() is not None

    def index_exists(name: str) -> bool:
        sql = "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?"
        return conn.execute(sql, (name,)).fetchone() is not None

    # 1) Colunas (checa antes de adicionar)
    if not has_column("registros", "criado_em"):
        conn.execute("ALTER TABLE registros ADD COLUMN criado_em TEXT")
    if not has_column("registros", "atualizado_em"):
        conn.execute("ALTER TABLE registros ADD COLUMN atualizado_em TEXT")
    if not has_column("registros", "origem"):
        conn.execute("ALTER TABLE registros ADD COLUMN origem TEXT")

    # 2) Backfill
    conn.execute(
        """
        UPDATE registros
           SET criado_em     = COALESCE(criado_em, CURRENT_TIMESTAMP),
               atualizado_em = COALESCE(atualizado_em, CURRENT_TIMESTAMP),
               origem        = COALESCE(origem, 'script_migracao')
         WHERE criado_em IS NULL
            OR atualizado_em IS NULL
            OR origem IS NULL
        """
    )

    # 3) Triggers — drop se existir e recria
    if trigger_exists("trg_registros_set_atualizado_em"):
        conn.execute("DROP TRIGGER trg_registros_set_atualizado_em")
    conn.executescript(
        """
        CREATE TRIGGER trg_registros_set_atualizado_em
        AFTER UPDATE ON registros
        FOR EACH ROW
        WHEN NEW.atualizado_em IS OLD.atualizado_em
        BEGIN
            UPDATE registros
               SET atualizado_em = CURRENT_TIMESTAMP
             WHERE id = NEW.id;
        END;
        """
    )

    if trigger_exists("trg_registros_set_criado_em_default"):
        conn.execute("DROP TRIGGER trg_registros_set_criado_em_default")
    conn.executescript(
        """
        CREATE TRIGGER trg_registros_set_criado_em_default
        AFTER INSERT ON registros
        FOR EACH ROW
        WHEN NEW.criado_em IS NULL
        BEGIN
            UPDATE registros
               SET criado_em = CURRENT_TIMESTAMP
             WHERE id = NEW.id;
        END;
        """
    )

    if trigger_exists("trg_registros_set_origem_default"):
        conn.execute("DROP TRIGGER trg_registros_set_origem_default")
    conn.executescript(
        """
        CREATE TRIGGER trg_registros_set_origem_default
        AFTER INSERT ON registros
        FOR EACH ROW
        WHEN NEW.origem IS NULL
        BEGIN
            UPDATE registros
               SET origem = 'script_migracao'
             WHERE id = NEW.id;
        END;
        """
    )

    # 4) Índices (checa antes de criar)
    if not index_exists("idx_registros_criado_em"):
        conn.execute("CREATE INDEX idx_registros_criado_em ON registros(criado_em)")
    if not index_exists("idx_registros_atualizado_em"):
        conn.execute(
            "CREATE INDEX idx_registros_atualizado_em ON registros(atualizado_em)"
        )
