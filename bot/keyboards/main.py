"""Главное меню — inline-кнопки для основных действий."""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard() -> types.InlineKeyboardMarkup:
    """Создаёт главное меню с кнопками действий."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Поиск сообщений", callback_data="action_search")
    builder.button(text="📊 Сводка за день", callback_data="action_summary")
    builder.button(text="⚙️ Настройки", callback_data="action_settings")
    builder.adjust(1)
    return builder.as_markup()
