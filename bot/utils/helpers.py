"""Вспомогательные функции для бота."""

import datetime
import re
from typing import Optional, Tuple


def parse_date(date_str: str) -> Optional[datetime.date]:
    """
    Парсит строку с датой в формате ГГГГ-ММ-ДД или ДД.ММ.ГГГГ.

    Параметры:
        date_str: Строка с датой

    Returns:
        Объект date или None, если формат не распознан
    """
    # ISO формат: 2024-01-15
    try:
        return datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        pass

    # Российский формат: 15.01.2024
    match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return datetime.date(year, month, day)
        except ValueError:
            pass

    return None


def format_date(date: datetime.date, fmt: str = "ru") -> str:
    """
    Форматирует дату в человекочитаемый вид.

    Параметры:
        date: Объект date
        fmt: Формат ("ru" — ДД.ММ.ГГГГ, "iso" — ГГГГ-ММ-ДД, "full" — с месяцем словами)

    Returns:
        Отформатированная строка с датой
    """
    if fmt == "iso":
        return date.isoformat()
    elif fmt == "full":
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        ]
        return f"{date.day} {months[date.month - 1]} {date.year} года"
    else:  # "ru"
        return date.strftime("%d.%m.%Y")


def split_long_text(text: str, max_length: int = 3500) -> list[str]:
    """
    Разбивает длинный текст на части для отправки через Telegram.

    Параметры:
        text: Исходный текст
        max_length: Максимальная длина одной части (по умолчанию 3500 символов)

    Returns:
        Список частей текста
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current = text

    while len(current) > max_length:
        # Ищем место разрыва по границе предложения или абзаца
        split_at = current.rfind("\n\n", 0, max_length)
        if split_at == -1:
            split_at = current.rfind(". ", 0, max_length)
        if split_at == -1:
            split_at = current.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = current.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length

        split_at += 1  # включаем разделитель
        parts.append(current[:split_at].strip())
        current = current[split_at:].strip()

    if current:
        parts.append(current)

    return parts


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Обрезает текст до указанной длины, добавляя многоточие.

    Параметры:
        text: Исходный текст
        max_length: Максимальная длина

    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def extract_channel_identifier(channel_id: int) -> str:
    """
    Извлекает идентификатор канала для построения ссылок.

    Параметры:
        channel_id: ID канала (может быть с префиксом -100)

    Returns:
        Строковый идентификатор без префикса -100
    """
    str_id = str(channel_id)
    if str_id.startswith("-100"):
        return str_id[4:]
    return str_id


def get_date_range(date: datetime.date) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Возвращает начало и конец дня в UTC.

    Параметры:
        date: Дата

    Returns:
        Кортеж (start_datetime, end_datetime)
    """
    start = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
    end = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)
    return start, end
