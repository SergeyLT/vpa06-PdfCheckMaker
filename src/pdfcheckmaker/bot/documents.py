"""Обработка файлов, присланных Telegram-пользователем."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram import Bot
from aiogram.types import FSInputFile, Message
from aiogram.utils.chat_action import ChatActionSender

from pdfcheckmaker.bot.config import BotSettings
from pdfcheckmaker.bot.messages import UNSUPPORTED_FILE_TEXT
from pdfcheckmaker.core.exceptions import (
    DataSourceError,
    InvoiceValidationError,
    PdfCheckMakerError,
    RenderError,
    TemplateError,
)
from pdfcheckmaker.services.generation import generate_pdfs_from_data_file

logger = logging.getLogger(__name__)

SUPPORTED_INPUT_EXTENSIONS = {".csv", ".json"}


class BotDocumentError(Exception):
    """Ошибка входного файла, понятная пользователю Telegram."""


def validate_document_file_name(file_name: str | None) -> str:
    """Проверить имя файла и вернуть его расширение."""
    suffix = Path(file_name or "").suffix.lower()
    if suffix not in SUPPORTED_INPUT_EXTENSIONS:
        raise BotDocumentError(UNSUPPORTED_FILE_TEXT)
    return suffix


def validate_document_size(file_size: int | None, settings: BotSettings) -> None:
    """Проверить размер Telegram-документа."""
    if file_size is None:
        raise BotDocumentError("Не удалось определить размер файла.")
    if file_size > settings.max_input_file_size_bytes:
        limit_mb = settings.max_input_file_size_bytes / 1024 / 1024
        raise BotDocumentError(
            f"Файл слишком большой. Максимальный размер: {limit_mb:.1f} МБ."
        )


def format_generation_error(error: PdfCheckMakerError) -> str:
    """Преобразовать внутреннюю ошибку генерации в понятный текст."""
    if isinstance(error, (DataSourceError, InvoiceValidationError)):
        return (
            "Не удалось прочитать данные из файла. Проверьте формат CSV/JSON "
            f"и обязательные поля. Детали: {error}"
        )
    if isinstance(error, (TemplateError, RenderError)):
        return f"Не удалось создать PDF по готовому шаблону. Детали: {error}"
    return f"Не удалось обработать файл. Детали: {error}"


async def process_document_message(
    message: Message,
    bot: Bot,
    settings: BotSettings,
    project_root: Path,
    template_dir: Path,
) -> bool:
    """Скачать CSV/JSON, сгенерировать PDF и отправить результат."""
    document = message.document
    if document is None:
        await message.answer(UNSUPPORTED_FILE_TEXT)
        return False

    try:
        suffix = validate_document_file_name(document.file_name)
        validate_document_size(document.file_size, settings)

        temp_root = project_root / "output" / "bot_tmp"
        temp_root.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory(prefix="telegram_", dir=temp_root) as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            data_file = temp_dir / f"input{suffix}"
            pdf_dir = temp_dir / "pdf"

            await bot.download(document, destination=data_file)

            async with ChatActionSender.upload_document(
                bot=bot,
                chat_id=message.chat.id,
            ):
                pdf_paths = generate_pdfs_from_data_file(
                    data_file,
                    template_dir,
                    pdf_dir,
                )

            for pdf_path in pdf_paths:
                await message.answer_document(
                    FSInputFile(pdf_path),
                    caption=f"Готово: {pdf_path.name}",
                )
        return True
    except BotDocumentError as exc:
        await message.answer(str(exc))
        return False
    except PdfCheckMakerError as exc:
        await message.answer(format_generation_error(exc))
        return False
    except Exception:
        logger.exception("Unexpected Telegram document processing error")
        await message.answer(
            "Не удалось обработать файл из-за внутренней ошибки. "
            "Попробуйте позже или обратитесь к администратору."
        )
        return False
