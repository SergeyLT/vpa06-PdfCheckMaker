"""Хэндлеры Telegram-бота."""

from __future__ import annotations

from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import Message

from pdfcheckmaker.bot.config import BotSettings
from pdfcheckmaker.bot.documents import process_document_message
from pdfcheckmaker.bot.keyboards import (
    TEMPLATE_CALLBACK_PREFIX,
    build_templates_keyboard,
    resolve_template_choice,
)
from pdfcheckmaker.bot.messages import HELP_TEXT, START_TEXT
from pdfcheckmaker.bot.states import InvoiceGenerationStates

router = Router(name="pdfcheckmaker_bot")


@router.message(CommandStart())
async def handle_start(message: Message, project_root: Path) -> None:
    """Ответить на команду /start."""
    await message.answer(
        START_TEXT,
        reply_markup=build_templates_keyboard(project_root),
    )


@router.message(Command("help"))
async def handle_help(message: Message, project_root: Path) -> None:
    """Ответить на команду /help."""
    await message.answer(
        HELP_TEXT,
        reply_markup=build_templates_keyboard(project_root),
    )


@router.callback_query(F.data.startswith(TEMPLATE_CALLBACK_PREFIX))
async def handle_template_choice(
    callback: CallbackQuery,
    state: FSMContext,
    project_root: Path,
) -> None:
    """Сохранить выбранный шаблон и попросить файл данных."""
    try:
        template_dir = resolve_template_choice(project_root, callback.data)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await state.update_data(template_dir=str(template_dir))
    await state.set_state(InvoiceGenerationStates.waiting_for_data_file)
    await callback.answer("Шаблон выбран")
    if callback.message is not None:
        await callback.message.answer(
            f"Выбран шаблон: {template_dir.name}. Теперь пришлите CSV или JSON."
        )


@router.message(F.document)
async def handle_document(
    message: Message,
    bot: Bot,
    settings: BotSettings,
    project_root: Path,
    state: FSMContext,
) -> None:
    """Обработать присланный CSV/JSON-документ."""
    data = await state.get_data()
    template_dir_value = data.get("template_dir")
    if not isinstance(template_dir_value, str):
        await message.answer(
            "Сначала выберите шаблон.",
            reply_markup=build_templates_keyboard(project_root),
        )
        return

    success = await process_document_message(
        message,
        bot,
        settings,
        project_root,
        Path(template_dir_value),
    )
    if success:
        await state.clear()
        await message.answer(
            "Готово. Для следующего файла выберите шаблон снова.",
            reply_markup=build_templates_keyboard(project_root),
        )
