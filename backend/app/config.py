from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://mashbot:mashbot@db:5432/mashbot"
    secret_key: str = "change-me-in-development"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

