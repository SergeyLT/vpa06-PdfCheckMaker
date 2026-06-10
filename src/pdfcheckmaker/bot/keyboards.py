"""Inline-клавиатуры Telegram-бота."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from pdfcheckmaker.templates_engine.loader import discover_templates
from pdfcheckmaker.templates_engine.manifest import TemplateManifest

TEMPLATE_CALLBACK_PREFIX = "template:"


@dataclass(frozen=True)
class TemplateChoice:
    """Шаблон, доступный пользователю бота."""

    index: int
    title: str
    path: Path

    @property
    def callback_data(self) -> str:
        return f"{TEMPLATE_CALLBACK_PREFIX}{self.index}"


def get_template_choices(project_root: Path) -> list[TemplateChoice]:
    """Получить список готовых шаблонов из templates/."""
    choices: list[TemplateChoice] = []
    for index, template_dir in enumerate(
        discover_templates(project_root / "templates"),
        start=1,
    ):
        choices.append(
            TemplateChoice(
                index=index,
                title=get_template_title(template_dir),
                path=template_dir,
            )
        )
    return choices


def get_template_title(template_dir: Path) -> str:
    """Вернуть человекочитаемое имя шаблона."""
    try:
        manifest = TemplateManifest.from_file(template_dir / "manifest.yaml")
    except Exception:
        return template_dir.name
    return manifest.title or manifest.name or template_dir.name


def build_templates_keyboard(project_root: Path) -> InlineKeyboardMarkup:
    """Собрать inline-кнопки для выбора шаблона."""
    builder = InlineKeyboardBuilder()
    for choice in get_template_choices(project_root):
        builder.button(text=choice.title, callback_data=choice.callback_data)
    builder.adjust(1)
    return builder.as_markup()


def resolve_template_choice(project_root: Path, callback_data: str | None) -> Path:
    """Найти шаблон по callback_data."""
    if callback_data is None or not callback_data.startswith(TEMPLATE_CALLBACK_PREFIX):
        raise ValueError("Некорректный выбор шаблона")

    raw_index = callback_data.removeprefix(TEMPLATE_CALLBACK_PREFIX)
    try:
        selected_index = int(raw_index)
    except ValueError as exc:
        raise ValueError("Некорректный выбор шаблона") from exc

    for choice in get_template_choices(project_root):
        if choice.index == selected_index:
            return choice.path
    raise ValueError("Выбранный шаблон больше недоступен")
