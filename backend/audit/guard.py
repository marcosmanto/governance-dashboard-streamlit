from backend.db import connect, query


def is_system_locked() -> bool:
    """
    Verifica se o sistema está em modo de bloqueio (Read-Only)
    devido a violação de auditoria.
    """
    conn = connect()
    try:
        rows = query(conn, "SELECT status FROM audit_integrity WHERE id = 1")
        if rows and rows[0]["status"] != "OK":
            return True
        return False
    except Exception:
        # Se a tabela não existir ou der erro, assume sistema aberto (fail-open)
        # para não travar antes das migrações rodarem.
        return False
    finally:
        conn.close()
