from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from backend.auth.users import authenticate
from backend.models import User

security = HTTPBasic()


def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> User:
    user = authenticate(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
