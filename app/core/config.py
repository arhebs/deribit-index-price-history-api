from __future__ import annotations

from functools import lru_cache
from typing import Annotated, ClassVar, final

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: Annotated[
        str, Field(description="SQLAlchemy database URL, e.g. postgresql+asyncpg://...")
    ] = ""
    redis_url: Annotated[
        str, Field(description="Redis URL, e.g. redis://localhost:6379/0")
    ] = ""
    deribit_base_url: Annotated[
        str,
        Field(
            description="Deribit API base URL (defaults to testnet)",
        ),
    ] = "https://test.deribit.com/api/v2"
    log_level: Annotated[str, Field(description="Application log level")] = "INFO"

    @field_validator("database_url", "redis_url")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("must be set")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
