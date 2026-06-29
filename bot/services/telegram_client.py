"""Сервис для работы с Telegram через Telethon (личный аккаунт)."""

import asyncio
import datetime
import logging
import random
from typing import List, Optional

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import Message, ForumTopic

logger = logging.getLogger(__name__)

# Константы для обработки flood wait
MAX_RETRIES = 5
BASE_DELAY = 1.0  # секунд
MAX_DELAY = 120.0  # максимальная задержка
JITTER_FACTOR = 0.25  # случайный разброс ±25%
PAGINATION_DELAY_MIN = 0.5  # мин задержка между страницами
PAGINATION_DELAY_MAX = 1.5  # макс задержка между страницами


class TelegramClientService:
    """Обёртка над Telethon для работы с каналами и сообщениями."""

    def __init__(
        self,
        session_path: str,
        api_id: int,
        api_hash: str,
        phone_number: str,
    ) -> None:
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client: Optional[TelegramClient] = None

    async def _safe_call(self, request_func, *args, **kwargs):
        """
        Безопасный вызов Telethon API с обработкой FloodWaitError.

        Использует экспоненциальную задержку с jitter и ограничением
        на количество повторных попыток.

        Args:
            request_func: Асинхронная функция для вызова API
            *args, **kwargs: Аргументы для функции

        Returns:
            Результат вызова API

        Raises:
            FloodWaitError: Если превышен лимит повторных попыток
        """
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await request_func(*args, **kwargs)
            except FloodWaitError as e:
                last_error = e
                wait_time = e.seconds if e.seconds > 0 else BASE_DELAY * (2 ** (attempt - 1))
                # Ограничиваем максимальное время ожидания
                wait_time = min(wait_time, MAX_DELAY)
                # Добавляем jitter (случайный разброс)
                jitter = wait_time * JITTER_FACTOR * random.uniform(-1, 1)
                total_wait = max(1.0, wait_time + jitter)

                logger.warning(
                    f"FloodWaitError (попытка {attempt}/{MAX_RETRIES}): "
                    f"ожидание {total_wait:.1f}с (исходно {wait_time:.0f}с) "
                    f"на {request_func.__name__ if hasattr(request_func, '__name__') else 'запросе'}"
                )

                await asyncio.sleep(total_wait)

        # Если все попытки исчерпаны
        logger.error(
            f"FloodWaitError: превышено количество попыток ({MAX_RETRIES}). "
            f"Последнее ожидание: {last_error.seconds}с"
        )
        raise last_error  # type: ignore[misc]

    async def start(self) -> None:
        """Запускает Telethon клиент и выполняет авторизацию."""
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone_number)
        logger.info("Telethon client успешно авторизован")

    async def stop(self) -> None:
        """Останавливает Telethon клиент."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telethon client отключён")

    async def get_dialogs(self) -> List[dict]:
        """
        Возвращает список доступных каналов (диалогов) пользователя.

        Returns:
            Список словарей с ключами: id, title
        """
        if not self.client:
            raise RuntimeError("Telethon client не инициализирован. Вызовите start()")

        dialogs = await self._safe_call(self.client.get_dialogs)
        channels = []

        for dialog in dialogs:
            if dialog.is_channel:
                channels.append({
                    "id": dialog.id,
                    "title": dialog.title or "Без названия",
                })

        # Сортируем по названию
        channels.sort(key=lambda ch: ch["title"].lower())
        logger.info(f"Получено {len(channels)} каналов")
        return channels

    async def get_forum_topics(self, channel_id: int) -> List[dict]:
        """
        Получает список топиков (тем форума) для канала/супергруппы.

        Args:
            channel_id: ID канала

        Returns:
            Список словарей с ключами: id, title
            Пустой список, если у канала нет форума.
        """
        if not self.client:
            raise RuntimeError("Telethon client не инициализирован")

        entity = await self._safe_call(self.client.get_entity, channel_id)

        try:
            # Используем вложенную функцию для корректной передачи вызова self.client(...)
            async def _fetch_topics():
                return await self.client(GetForumTopicsRequest(
                    channel=entity,
                    offset_date=None,
                    offset_id=0,
                    offset_topic=0,
                    limit=100,
                    q=None,
                ))

            result = await self._safe_call(_fetch_topics)

            topics = []
            for topic in result.topics:
                if isinstance(topic, ForumTopic):
                    topics.append({
                        "id": topic.id,
                        "title": topic.title,
                    })

            logger.info(
                f"Получено {len(topics)} топиков форума для канала {channel_id}"
            )
            return topics

        except FloodWaitError as e:
            # Flood wait на GetForumTopicsRequest — логируем и возвращаем пустой список
            logger.warning(
                f"FloodWaitError при получении топиков для канала {channel_id}: "
                f"ожидание {e.seconds}с. Пропускаем топики."
            )
            return []
        except Exception as e:
            # Если канал не является форумом — возвращаем пустой список
            logger.info(
                f"Канал {channel_id} не имеет форума или произошла ошибка: {e}"
            )
            return []

    async def search_messages(
        self,
        channel_id: int,
        date: datetime.date,
        query: str,
        limit: int = 50,
        topic_id: Optional[int] = None,
    ) -> List[Message]:
        """
        Ищет сообщения в канале по ключевым словам за указанную дату.

        Параметры:
            channel_id: ID канала
            date: Дата для поиска
            query: Ключевые слова для поиска
            limit: Максимальное количество сообщений
            topic_id: ID топика форума (если None — ищет по всему каналу)

        Returns:
            Список найденных сообщений Telethon
        """
        if not self.client:
            raise RuntimeError("Telethon client не инициализирован")

        # Вычисляем временной диапазон
        start_date = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)

        entity = await self._safe_call(self.client.get_entity, channel_id)

        messages = await self._safe_call(
            self.client.get_messages,
            entity,
            limit=limit,
            offset_date=end_date,
            search=query,
        )

        # Фильтруем по дате (Telethon может вернуть сообщения за другие даты)
        filtered = [
            msg for msg in messages
            if msg.date and start_date <= msg.date <= end_date
        ]

        # Фильтруем по топику, если указан
        if topic_id is not None:
            filtered = [
                msg for msg in filtered
                if msg.reply_to_msg_id == topic_id
            ]

        logger.info(
            f"Поиск в канале {channel_id}: запрос '{query}' за {date}, "
            f"топик {topic_id}, найдено {len(filtered)} из {len(messages)} сообщений"
        )
        return filtered

    async def get_messages(
        self,
        channel_id: int,
        date: datetime.date,
        limit: int = 50,
        topic_id: Optional[int] = None,
    ) -> List[Message]:
        """
        Получает все сообщения из канала за указанную дату.

        Параметры:
            channel_id: ID канала
            date: Дата для получения сообщений
            limit: Максимальное количество сообщений (по умолчанию 50)
            topic_id: ID топика форума (если None — получает по всему каналу)

        Returns:
            Список сообщений Telethon
        """
        if not self.client:
            raise RuntimeError("Telethon client не инициализирован")

        start_date = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)

        entity = await self._safe_call(self.client.get_entity, channel_id)

        # Загружаем сообщения порциями для преодоления лимита
        all_messages = []
        offset_id = 0
        page = 0

        while len(all_messages) < limit:
            page += 1
            batch_size = min(50, limit - len(all_messages))

            messages = await self._safe_call(
                self.client.get_messages,
                entity,
                limit=batch_size,
                offset_id=offset_id,
                offset_date=end_date,
            )

            if not messages:
                break

            # Фильтруем по дате
            filtered = [
                msg for msg in messages
                if msg.date and start_date <= msg.date <= end_date
            ]

            # Фильтруем по топику, если указан
            if topic_id is not None:
                filtered = [
                    msg for msg in filtered
                    if msg.reply_to_msg_id == topic_id
                ]

            all_messages.extend(filtered)

            logger.debug(
                f"Страница {page}: получено {len(messages)} сообщений, "
                f"отфильтровано {len(filtered)}, всего {len(all_messages)}"
            )

            # Если последнее сообщение старше start_date — выходим
            if messages[-1].date and messages[-1].date < start_date:
                break

            offset_id = messages[-1].id

            # Задержка между страницами для избежания flood wait
            if len(all_messages) < limit:
                delay = random.uniform(PAGINATION_DELAY_MIN, PAGINATION_DELAY_MAX)
                await asyncio.sleep(delay)

        logger.info(
            f"Получено {len(all_messages)} сообщений из канала {channel_id} "
            f"за {date}, топик {topic_id} (страниц: {page})"
        )
        return all_messages
