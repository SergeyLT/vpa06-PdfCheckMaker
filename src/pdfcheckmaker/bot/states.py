"""FSM-состояния Telegram-бота."""

from aiogram.fsm.state import State, StatesGroup


class InvoiceGenerationStates(StatesGroup):
    """Сценарий генерации PDF: шаблон выбран, ожидаем файл."""

    waiting_for_data_file = State()
