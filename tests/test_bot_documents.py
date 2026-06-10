import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pdfcheckmaker.bot.config import BotSettings
from pdfcheckmaker.bot.documents import (
    BotDocumentError,
    format_generation_error,
    process_document_message,
    validate_document_file_name,
    validate_document_size,
)
from pdfcheckmaker.bot.messages import UNSUPPORTED_FILE_TEXT
from pdfcheckmaker.core.exceptions import DataSourceError


class DummyChatAction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def make_settings(max_size: int = 1024) -> BotSettings:
    return BotSettings(
        BOT_TOKEN="123456:test-token",
        ALLOWED_USER_IDS="1001",
        MAX_INPUT_FILE_SIZE_BYTES=max_size,
    )


def test_validate_document_file_name_accepts_csv_and_json() -> None:
    assert validate_document_file_name("invoices.csv") == ".csv"
    assert validate_document_file_name("invoices.JSON") == ".json"


def test_validate_document_file_name_rejects_other_formats() -> None:
    with pytest.raises(BotDocumentError, match=UNSUPPORTED_FILE_TEXT):
        validate_document_file_name("invoice.xlsx")


def test_validate_document_size_rejects_large_file() -> None:
    with pytest.raises(BotDocumentError, match="слишком большой"):
        validate_document_size(2048, make_settings(max_size=1024))


def test_format_generation_error_for_invalid_data() -> None:
    text = format_generation_error(DataSourceError("bad csv"))

    assert "Не удалось прочитать данные" in text
    assert "bad csv" in text


def test_process_document_message_generates_and_sends_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_dir = tmp_path / "templates" / "invoice_standard"
    template_dir.mkdir(parents=True)
    (template_dir / "manifest.yaml").write_text("name: test", encoding="utf-8")

    def fake_generate(
        data_file: Path,
        selected_template_dir: Path,
        output_dir: Path,
    ) -> list[Path]:
        assert data_file.read_text(encoding="utf-8") == "invoice_id\nINV-1\n"
        assert selected_template_dir == template_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / "invoice_INV-1.pdf"
        pdf_path.write_bytes(b"%PDF-test")
        return [pdf_path]

    monkeypatch.setattr(
        "pdfcheckmaker.bot.documents.generate_pdfs_from_data_file",
        fake_generate,
    )
    monkeypatch.setattr(
        "pdfcheckmaker.bot.documents.ChatActionSender.upload_document",
        lambda **_: DummyChatAction(),
    )

    async def fake_download(document: object, destination: Path) -> None:
        destination.write_text("invoice_id\nINV-1\n", encoding="utf-8")

    message = SimpleNamespace(
        document=SimpleNamespace(file_name="invoices.csv", file_size=100),
        chat=SimpleNamespace(id=1001),
        answer=AsyncMock(),
        answer_document=AsyncMock(),
    )
    bot = SimpleNamespace(download=AsyncMock(side_effect=fake_download))

    result = asyncio.run(
        process_document_message(message, bot, make_settings(), tmp_path, template_dir)
    )

    assert result is True
    bot.download.assert_awaited_once()
    message.answer.assert_not_awaited()
    message.answer_document.assert_awaited_once()
    assert not any((tmp_path / "output" / "bot_tmp").glob("telegram_*"))


def test_process_document_message_reports_unsupported_file(tmp_path: Path) -> None:
    message = SimpleNamespace(
        document=SimpleNamespace(file_name="invoices.xlsx", file_size=100),
        answer=AsyncMock(),
    )
    bot = SimpleNamespace(download=AsyncMock())

    template_dir = tmp_path / "templates" / "invoice_standard"

    result = asyncio.run(
        process_document_message(message, bot, make_settings(), tmp_path, template_dir)
    )

    assert result is False
    message.answer.assert_awaited_once_with(UNSUPPORTED_FILE_TEXT)
    bot.download.assert_not_awaited()
