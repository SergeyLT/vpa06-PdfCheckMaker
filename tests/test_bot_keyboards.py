from pathlib import Path

import pytest

from pdfcheckmaker.bot.keyboards import (
    build_templates_keyboard,
    get_template_choices,
    resolve_template_choice,
)


def make_template(root: Path, name: str, title: str) -> Path:
    template_dir = root / "templates" / name
    template_dir.mkdir(parents=True)
    (template_dir / "manifest.yaml").write_text(
        f"name: {name}\ntitle: {title}\n",
        encoding="utf-8",
    )
    return template_dir


def test_get_template_choices_reads_titles(tmp_path: Path) -> None:
    template_dir = make_template(tmp_path, "invoice_standard", "Стандартный чек")

    choices = get_template_choices(tmp_path)

    assert len(choices) == 1
    assert choices[0].title == "Стандартный чек"
    assert choices[0].path == template_dir
    assert choices[0].callback_data == "template:1"


def test_build_templates_keyboard_contains_buttons(tmp_path: Path) -> None:
    make_template(tmp_path, "invoice_standard", "Стандартный чек")

    keyboard = build_templates_keyboard(tmp_path)

    assert keyboard.inline_keyboard[0][0].text == "Стандартный чек"
    assert keyboard.inline_keyboard[0][0].callback_data == "template:1"


def test_resolve_template_choice_returns_path(tmp_path: Path) -> None:
    template_dir = make_template(tmp_path, "invoice_standard", "Стандартный чек")

    assert resolve_template_choice(tmp_path, "template:1") == template_dir


def test_resolve_template_choice_rejects_bad_callback(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Некорректный выбор"):
        resolve_template_choice(tmp_path, "bad:1")
