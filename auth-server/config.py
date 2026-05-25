import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./oauth2.db",  # default for local dev without Docker
)

SECRET_KEY = os.getenv("AUTH_SERVER_SECRET_KEY", "change-me-in-production")
ALGORITHM = os.getenv("AUTH_SERVER_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
AUTHORIZATION_CODE_EXPIRE_MINUTES = int(os.getenv("AUTHORIZATION_CODE_EXPIRE_MINUTES", "10"))
