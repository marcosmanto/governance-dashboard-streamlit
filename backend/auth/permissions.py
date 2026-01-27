from fastapi import HTTPException, status

from backend.models import User


def require_role(*allowed_roles: str):
    def checker(user: User):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )

    return checker
