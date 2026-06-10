import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pdfcheckmaker.bot.handlers import (
    handle_document,
    handle_help,
    handle_start,
    handle_template_choice,
)
from pdfcheckmaker.bot.messages import HELP_TEXT, START_TEXT


def test_handle_start_answers_in_russian() -> None:
    message = AsyncMock()
    project_root = Path("project")

    asyncio.run(handle_start(message, project_root))

    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0] == START_TEXT
    assert message.answer.await_args.kwargs["reply_markup"] is not None


def test_handle_help_answers_in_russian() -> None:
    message = AsyncMock()
    project_root = Path("project")

    asyncio.run(handle_help(message, project_root))

    message.answer.assert_awaited_once()
    assert message.answer.await_args.args[0] == HELP_TEXT
    assert message.answer.await_args.kwargs["reply_markup"] is not None


def test_handle_template_choice_saves_state(
    tmp_path: Path, monkeypatch: object
) -> None:
    template_dir = tmp_path / "templates" / "invoice_standard"
    template_dir.mkdir(parents=True)
    (template_dir / "manifest.yaml").write_text("name: standard", encoding="utf-8")
    state = AsyncMock()
    callback = SimpleNamespace(
        data="template:1",
        answer=AsyncMock(),
        message=SimpleNamespace(answer=AsyncMock()),
    )

    asyncio.run(handle_template_choice(callback, state, tmp_path))

    state.update_data.assert_awaited_once_with(template_dir=str(template_dir))
    state.set_state.assert_awaited_once()
    callback.answer.assert_awaited_once_with("Шаблон выбран")
    callback.message.answer.assert_awaited_once()


def test_handle_document_requires_template_choice() -> None:
    message = AsyncMock()
    state = AsyncMock()
    state.get_data.return_value = {}

    asyncio.run(
        handle_document(
            message,
            AsyncMock(),
            AsyncMock(),
            Path("project"),
            state,
        )
    )

    message.answer.assert_awaited_once()
    assert "Сначала выберите шаблон" in message.answer.await_args.args[0]


def test_handle_document_clears_state_after_success(
    tmp_path: Path, monkeypatch: object
) -> None:
    template_dir = tmp_path / "templates" / "invoice_standard"
    template_dir.mkdir(parents=True)
    state = AsyncMock()
    state.get_data.return_value = {"template_dir": str(template_dir)}
    message = AsyncMock()

    async def fake_process_document_message(*args: object) -> bool:
        return True

    monkeypatch.setattr(
        "pdfcheckmaker.bot.handlers.process_document_message",
        fake_process_document_message,
    )

    asyncio.run(
        handle_document(
            message,
            AsyncMock(),
            AsyncMock(),
            tmp_path,
            state,
        )
    )

    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()
