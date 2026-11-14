from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    admin_username: str = "admin"
    admin_password_hash: str = ""
    secret_key: str = "dev-secret-key-change-me"

    database_path: Path = BACKEND_DIR / "orders.db"
    uploads_dir: Path = BACKEND_DIR / "uploads"
    max_upload_size_bytes: int = 300 * 1024 * 1024

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    frontend_dist_dir: Path = BACKEND_DIR.parent / "frontend" / "dist"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
