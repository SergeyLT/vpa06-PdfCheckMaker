import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pdfcheckmaker.bot.messages import ACCESS_DENIED_TEXT
from pdfcheckmaker.bot.middleware import UserWhitelistMiddleware


def test_whitelist_middleware_allows_known_user() -> None:
    middleware = UserWhitelistMiddleware((1001,))
    handler = AsyncMock(return_value="ok")
    event = SimpleNamespace(from_user=SimpleNamespace(id=1001), answer=AsyncMock())

    result = asyncio.run(middleware(handler, event, {}))

    assert result == "ok"
    handler.assert_awaited_once_with(event, {})
    event.answer.assert_not_awaited()


def test_whitelist_middleware_rejects_unknown_user() -> None:
    middleware = UserWhitelistMiddleware((1001,))
    handler = AsyncMock()
    event = SimpleNamespace(from_user=SimpleNamespace(id=2002), answer=AsyncMock())

    result = asyncio.run(middleware(handler, event, {}))

    assert result is None
    handler.assert_not_awaited()
    event.answer.assert_awaited_once_with(ACCESS_DENIED_TEXT)
