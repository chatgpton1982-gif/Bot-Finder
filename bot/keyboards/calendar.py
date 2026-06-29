"""Inline-календарь для выбора даты."""

import calendar
import datetime
from typing import Optional

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CalendarCallbackData(CallbackData, prefix="calendar"):
    """Callback data для календаря."""
    action: str  # "select" | "prev_month" | "next_month"
    year: int
    month: int
    day: int = 0


def _build_day_button(year: int, month: int, day: int) -> types.InlineKeyboardButton:
    """Создаёт кнопку для одного дня месяца."""
    return types.InlineKeyboardButton(
        text=str(day),
        callback_data=CalendarCallbackData(
            action="select",
            year=year,
            month=month,
            day=day,
        ).pack(),
    )


def get_calendar_keyboard(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> types.InlineKeyboardMarkup:
    """
    Создаёт inline-календарь для выбора даты.

    Параметры:
        year: Год (по умолчанию текущий)
        month: Месяц (по умолчанию текущий)
    """
    now = datetime.datetime.now()
    year = year or now.year
    month = month or now.month

    builder = InlineKeyboardBuilder()

    # Заголовок с месяцем и годом
    month_name = calendar.month_name[month]
    builder.row(
        types.InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data="calendar_ignore",
        )
    )

    # Дни недели
    row_days = []
    for day_name in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        row_days.append(
            types.InlineKeyboardButton(text=day_name, callback_data="calendar_ignore")
        )
    builder.row(*row_days)

    # Дни месяца — построчно
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(
                    types.InlineKeyboardButton(text=" ", callback_data="calendar_ignore")
                )
            else:
                row.append(_build_day_button(year, month, day))
        builder.row(*row)

    # Навигация
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    builder.row(
        types.InlineKeyboardButton(
            text="◀️",
            callback_data=CalendarCallbackData(
                action="prev_month",
                year=prev_year,
                month=prev_month,
                day=0,
            ).pack(),
        ),
        types.InlineKeyboardButton(
            text="Сегодня",
            callback_data=CalendarCallbackData(
                action="select",
                year=now.year,
                month=now.month,
                day=now.day,
            ).pack(),
        ),
        types.InlineKeyboardButton(
            text="▶️",
            callback_data=CalendarCallbackData(
                action="next_month",
                year=next_year,
                month=next_month,
                day=0,
            ).pack(),
        ),
    )

    return builder.as_markup()
