import logging
from datetime import datetime, timezone

from backend.auth.passwords import hash_password
from backend.db import connect, execute, query

# Configura logger para aparecer no docker logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERS = [
    ("admin", "admin", "admin", "email01@test.com"),
    ("editor", "editor", "editor", "email02@test.com"),
    ("leitor", "leitor", "reader", "email03@test.com"),
]


def create_inicial_users():
    conn = connect()
    try:
        for username, password, role, email in USERS:
            # Verifica se usuário já existe
            existing = query(conn, "SELECT 1 FROM users WHERE username = :u", {"u": username})

            if existing:
                logger.info(f"⚠️ Usuário '{username}' já existe. Mantendo senha atual.")
                continue

            execute(
                conn,
                """
                INSERT INTO users
                    (username, password_hash, role, email, created_at, must_change_password)
                VALUES
                    (:username, :password_hash, :role, :email, :created_at, 1)
                """,
                {
                    "username": username,
                    "password_hash": hash_password(password),
                    "role": role,
                    "email": email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            logger.info(f"✅ Usuário '{username}' criado.")
            conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_inicial_users()
