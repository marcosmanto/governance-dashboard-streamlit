from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Gera hash seguro (bcrypt) para senha em texto plano.
    """
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica se a senha informada corresponde ao hash armazenado.
    """
    return _pwd_context.verify(password, password_hash)
