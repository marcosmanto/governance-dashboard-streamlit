from backend.db import connect as get_connection

# shim de compatibilidade para antigo código
__all__ = ["get_connection"]
