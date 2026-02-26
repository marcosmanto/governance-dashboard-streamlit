from backend.core.logger import logger
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
    except Exception as e:
        # 🛡️ Fail-closed: Se houver erro ao checar integridade, BLOQUEIA o sistema.
        # Isso impede escritas em um banco instável ou corrompido.
        logger.critical(f"FALHA CRÍTICA NO GUARD: {e}")
        return True
    finally:
        conn.close()
