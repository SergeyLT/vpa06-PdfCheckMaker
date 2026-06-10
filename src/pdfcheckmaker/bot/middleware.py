"""Middleware для ограничения доступа к Telegram-боту."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from pdfcheckmaker.bot.messages import ACCESS_DENIED_TEXT


class UserWhitelistMiddleware(BaseMiddleware):
    """Пропускает только пользователей из белого списка."""

    def __init__(self, allowed_user_ids: tuple[int, ...]) -> None:
        self.allowed_user_ids = frozenset(allowed_user_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None and user.id in self.allowed_user_ids:
            return await handler(event, data)

        answer = getattr(event, "answer", None)
        if callable(answer):
            await answer(ACCESS_DENIED_TEXT)
        return None
