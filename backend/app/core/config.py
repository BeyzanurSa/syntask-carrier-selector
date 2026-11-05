from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Backend settings, read from environment variables and backend/.env."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # SecretStr keeps the key out of repr() and logs.
    typesafe_api_key: SecretStr | None = None
    frontend_origin: str = "http://localhost:3000"
