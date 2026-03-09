class DBError(Exception):
    """Erro genérico de banco independente de SGBD."""


class DuplicateKeyError(DBError):
    """Violação de chave única/índice UNIQUE."""


class ForeignKeyError(DBError):
    """Violação de chave estrangeira."""


class NotFoundError(DBError):
    """Registro não encontrado (uso opcional no CRUD)."""
