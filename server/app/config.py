"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "dev"
    db_password: str = "devpass"
    db_name: str = "gaokao_companion"

    # Test Database
    test_db_host: str = "localhost"
    test_db_port: int = 5433
    test_db_user: str = "dev"
    test_db_password: str = "devpass"
    test_db_name: str = "gaokao_companion_test"

    # JWT
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_hours: int = 168  # 7 days

    # WeChat
    wx_app_id: str = ""
    wx_app_secret: str = ""

    # Tencent Cloud COS
    cos_bucket: str = ""
    cos_region: str = "ap-shanghai"
    cos_secret_id: str = ""
    cos_secret_key: str = ""

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for Alembic migrations."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def test_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.test_db_user}:{self.test_db_password}"
            f"@{self.test_db_host}:{self.test_db_port}/{self.test_db_name}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
