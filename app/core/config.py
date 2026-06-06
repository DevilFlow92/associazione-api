from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "changeme"

    # Database
    database_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/associazione_db"
    )


settings = Settings()
