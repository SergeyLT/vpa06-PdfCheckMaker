"""Настройки Telegram-бота."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class BotSettings(BaseSettings):
    """Конфигурация бота из переменных окружения и .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(validation_alias="BOT_TOKEN")
    allowed_user_ids: Annotated[
        tuple[int, ...],
        NoDecode,
    ] = Field(
        default=(),
        validation_alias="ALLOWED_USER_IDS",
    )
    max_input_file_size_bytes: int = Field(
        default=5 * 1024 * 1024,
        gt=0,
        validation_alias="MAX_INPUT_FILE_SIZE_BYTES",
    )

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value: Any) -> Any:
        """Принять список ID в формате 1,2,3 из .env."""
        if value is None or value == "":
            return ()
        if isinstance(value, str):
            return tuple(
                int(user_id.strip()) for user_id in value.split(",") if user_id.strip()
            )
        return value


def load_settings() -> BotSettings:
    """Загрузить настройки Telegram-бота."""
    return BotSettings()
