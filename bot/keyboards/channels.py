"""Клавиатура для выбора канала из списка доступных."""

from typing import List

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_channels_keyboard(channels: List[dict]) -> types.InlineKeyboardMarkup:
    """
    Создаёт inline-клавиатуру со списком каналов.

    Каждый канал представлен в виде словаря с ключами:
        - id: int
        - title: str
    """
    builder = InlineKeyboardBuilder()

    for ch in channels:
        title = ch["title"][:40] if ch["title"] else "Без названия"
        builder.button(text=title, callback_data=f"channel:{ch['id']}")

    builder.adjust(1)
    return builder.as_markup()
