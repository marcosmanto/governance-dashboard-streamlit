from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from backend.auth.users import authenticate
from backend.models import User

security = HTTPBasic()


def get_current_user(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
) -> User:
    user = authenticate(credentials.username, credentials.password)
    request.state.user = user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
