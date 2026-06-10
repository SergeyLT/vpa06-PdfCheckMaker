import pytest
from pydantic import ValidationError

from pdfcheckmaker.bot.config import BotSettings


def test_bot_settings_parse_allowed_user_ids() -> None:
    settings = BotSettings(
        _env_file=None,
        BOT_TOKEN="123456:test-token",
        ALLOWED_USER_IDS="123, 456",
    )

    assert settings.bot_token == "123456:test-token"
    assert settings.allowed_user_ids == (123, 456)
    assert settings.max_input_file_size_bytes == 5 * 1024 * 1024


def test_bot_settings_require_token() -> None:
    with pytest.raises(ValidationError):
        BotSettings(_env_file=None, ALLOWED_USER_IDS="123")


def test_bot_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:test-token")
    monkeypatch.setenv("ALLOWED_USER_IDS", "123,456")

    settings = BotSettings()

    assert settings.allowed_user_ids == (123, 456)
