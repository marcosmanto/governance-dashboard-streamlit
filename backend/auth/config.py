import os
from datetime import timedelta

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"

# ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
ACCESS_TOKEN_EXPIRE = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)))

# REFRESH_TOKEN_EXPIRE = timedelta(days=7)
REFRESH_TOKEN_EXPIRE = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))
