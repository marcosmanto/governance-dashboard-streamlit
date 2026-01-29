from datetime import datetime, timezone

from backend.auth.passwords import hash_password
from backend.db import connect, execute

USERS = [
    ("admin", "admin", "admin"),
    ("editor", "editor", "editor"),
    ("leitor", "leitor", "leitor"),
]


def create_inicial_users():
    conn = connect()
    try:
        for username, password, role in USERS:
            execute(
                conn,
                """
                INSERT OR IGNORE INTO users
                    (username, password_hash, role, created_at)
                VALUES
                    (:username, :password_hash, :role, :created_at)
                """,
                {
                    "username": username,
                    "password_hash": hash_password(password),
                    "role": role,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_inicial_users()
    print("Usuários iniciais criados com sucesso.")
