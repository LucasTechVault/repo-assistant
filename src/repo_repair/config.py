"""Validated application configuration; construction has no filesystem side effects."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Load explicit values, environment, cwd .env, then defaults, in that order."""

    model_config = SettingsConfigDict(
        env_prefix="REPO_REPAIR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    repo_path: Path = Path(".")
    log_level: LogLevel = "INFO"

    @field_validator("repo_path")
    @classmethod
    def normalize_repo_path(cls, value: Path) -> Path:
        """Expand home references and resolve relative paths against the caller's cwd."""
        return value.expanduser().resolve()
