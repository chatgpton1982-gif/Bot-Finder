"""Middleware для ограничения доступа к боту по user_id."""

import logging
import os
from typing import Any, Awaitable, Callable, Dict, Set

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = logging.getLogger(__name__)


def _load_allowed_user_ids() -> Set[int]:
    """
    Загружает список разрешённых user_id из переменной окружения ALLOWED_USER_IDS.

    Формат: через запятую, например "123456789,987654321"
    Если переменная не установлена — доступ открыт для всех.
    """
    raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    if not raw:
        return set()
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки авторизации пользователя.

    Если ALLOWED_USER_IDS задан — пропускает только указанных пользователей.
    Если ALLOWED_USER_IDS пуст или не задан — пропускает всех.
    """

    def __init__(self) -> None:
        self.allowed_ids: Set[int] = _load_allowed_user_ids()
        if self.allowed_ids:
            logger.info(
                f"AuthMiddleware: доступ ограничен, разрешены user_id: {self.allowed_ids}"
            )
        else:
            logger.info("AuthMiddleware: доступ открыт для всех пользователей")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Извлекаем пользователя из события
        user: User | None = data.get("event_from_user")

        if user is None:
            # Не удалось определить пользователя — пропускаем
            return await handler(event, data)

        # Если список пуст — доступ для всех
        if not self.allowed_ids:
            return await handler(event, data)

        # Проверяем, входит ли пользователь в список разрешённых
        if user.id not in self.allowed_ids:
            logger.warning(
                f"AuthMiddleware: отклонён доступ для user_id={user.id} "
                f"(username={user.username})"
            )
            # Пытаемся отправить сообщение об отказе
            try:
                if hasattr(event, "answer"):
                    await event.answer(
                        "⛔ У вас нет доступа к этому боту.\n"
                        "Обратитесь к администратору."
                    )
                elif hasattr(event, "message") and event.message:
                    await event.message.answer(
                        "⛔ У вас нет доступа к этому боту.\n"
                        "Обратитесь к администратору."
                    )
            except Exception:
                pass
            return  # Не вызываем handler

        return await handler(event, data)