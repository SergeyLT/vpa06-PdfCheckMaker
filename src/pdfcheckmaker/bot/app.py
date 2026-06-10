"""Точка входа Telegram-бота."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from pdfcheckmaker.bot.config import BotSettings, load_settings
from pdfcheckmaker.bot.handlers import router
from pdfcheckmaker.bot.middleware import UserWhitelistMiddleware


def create_bot(settings: BotSettings) -> Bot:
    """Создать экземпляр aiogram Bot."""
    return Bot(token=settings.bot_token)


def create_dispatcher(
    settings: BotSettings, project_root: Path | None = None
) -> Dispatcher:
    """Собрать Dispatcher с роутерами и middleware."""
    dispatcher = Dispatcher(
        settings=settings,
        project_root=project_root or Path.cwd(),
    )
    dispatcher.message.middleware(UserWhitelistMiddleware(settings.allowed_user_ids))
    dispatcher.include_router(router)
    return dispatcher


async def run_bot(settings: BotSettings | None = None) -> None:
    """Запустить long polling Telegram-бота."""
    actual_settings = settings or load_settings()
    bot = create_bot(actual_settings)
    dispatcher = create_dispatcher(actual_settings)
    await dispatcher.start_polling(bot)


def main() -> None:
    """CLI-точка входа для запуска Telegram-бота."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(run_bot())
