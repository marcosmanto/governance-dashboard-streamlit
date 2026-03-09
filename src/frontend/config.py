from pydantic_settings import BaseSettings


class FrontendSettings(BaseSettings):
    # Apenas configurações necessárias para a UI
    ENV: str = "dev"
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8501"
    SSL_VERIFY: bool = True  # Padrão seguro

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignora variáveis do backend (DB_DSN, JWT_SECRET, etc)


settings = FrontendSettings()
