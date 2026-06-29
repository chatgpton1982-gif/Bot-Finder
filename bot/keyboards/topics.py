"""Клавиатура для выбора топика (темы форума) внутри канала."""

from typing import List

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_topics_keyboard(topics: List[dict], channel_id: int) -> types.InlineKeyboardMarkup:
    """
    Создаёт inline-клавиатуру со списком топиков форума.

    Каждый топик представлен в виде словаря с ключами:
        - id: int
        - title: str

    Args:
        topics: Список топиков
        channel_id: ID канала (для callback_data)

    Returns:
        InlineKeyboardMarkup с кнопками топиков
    """
    builder = InlineKeyboardBuilder()

    for topic in topics:
        title = topic["title"][:40] if topic["title"] else "Без названия"
        builder.button(
            text=f"💬 {title}",
            callback_data=f"topic:{channel_id}:{topic['id']}",
        )

    # Кнопка "Весь канал" (без фильтрации по топику)
    builder.button(
        text="📋 Весь канал",
        callback_data=f"topic:{channel_id}:all",
    )

    builder.adjust(1)
    return builder.as_markup()
