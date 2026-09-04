"""Application settings.

Every value here has a counterpart in the settings modules the project used
before: the secret key, the database location, the media/static roots, the
locale configuration, the token lifetimes and the API documentation metadata.
Values are read from the environment (or a ``.env`` file) and fall back to the
same defaults the project shipped with.
"""

from __future__ import annotations

import secrets
from datetime import timedelta
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str | None = None
    debug: bool = True

    @model_validator(mode="after")
    def _resolve_secret_key(self) -> "Settings":
        """Mirror the original's ``config('SECRET_KEY', default=get_random_secret_key())``
        while refusing to boot a non-debug deployment without a stable key: a random
        per-process key silently invalidates every issued token on restart and breaks
        multi-worker setups."""
        if not self.secret_key:
            if not self.debug:
                raise ValueError(
                    "SECRET_KEY must be set when DEBUG is false; "
                    "a random per-process key would invalidate tokens on every restart."
                )
            self.secret_key = secrets.token_urlsafe(50)
        return self

    database_url: str = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"

    language_code: str = "fa-ir"
    time_zone: str = "UTC"
    locale_dir: Path = BASE_DIR / "locale"
    translation_domain: str = "django"
    api_translation_domain: str = "api"

    static_url: str = "/static/"
    static_root: Path = BASE_DIR / "static"
    media_url: str = "/media/"
    media_root: Path = BASE_DIR / "media"

    jwt_algorithm: str = "HS256"
    access_token_lifetime: timedelta = timedelta(days=5000)
    refresh_token_lifetime: timedelta = timedelta(days=5000)

    api_title: str = "wall API"
    api_description: str = "an API doc for wall project"
    api_version: str = "1.0.0"

    @property
    def language(self) -> str:
        """The locale directory name matching ``language_code`` (``fa-ir`` -> ``fa_IR``)."""
        parts = self.language_code.replace("-", "_").split("_")
        if len(parts) == 1:
            return parts[0].lower()
        return f"{parts[0].lower()}_{parts[1].upper()}"


settings = Settings()
