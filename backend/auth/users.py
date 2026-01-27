from backend.models import User

USERS = {
    "leitor": {
        "password": "leitor123",
        "role": "reader",
    },
    "editor": {
        "password": "editor123",
        "role": "editor",
    },
    "admin": {
        "password": "admin123",
        "role": "admin",
    },
}


def authenticate(username: str, password: str) -> User | None:
    user = USERS.get(username)
    if not user:
        return None
    if user["password"] != password:
        return None
    return User(username=username, role=user["role"])
