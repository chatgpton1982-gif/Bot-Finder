"""Работа с SQLite базой данных."""

import datetime
import logging
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Управление SQLite базой данных."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Инициализирует БД и создаёт таблицы при необходимости."""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row

        await self._create_tables()
        logger.info(f"База данных инициализирована: {self.db_path}")

    async def _create_tables(self) -> None:
        """Создаёт таблицы, если их нет."""
        await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS cached_channels (
                channel_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                username TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                channel_title TEXT,
                search_date TEXT NOT NULL,
                query TEXT,
                action_type TEXT NOT NULL DEFAULT 'search',
                result_summary TEXT,
                messages_count INTEGER DEFAULT 0,
                topic_id INTEGER,
                topic_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.connection.commit()

    async def cache_channel(self, channel_id: int, title: str, username: Optional[str] = None) -> None:
        """Сохраняет или обновляет информацию о канале в кэше."""
        await self.connection.execute(
            """
            INSERT INTO cached_channels (channel_id, title, username, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(channel_id) DO UPDATE SET
                title = excluded.title,
                username = excluded.username,
                last_updated = CURRENT_TIMESTAMP
            """,
            (channel_id, title, username),
        )
        await self.connection.commit()

    async def save_search_history(
        self,
        channel_id: int,
        channel_title: str,
        search_date: str,
        query: str,
        action_type: str,
        result_summary: str = "",
        messages_count: int = 0,
        topic_id: Optional[int] = None,
        topic_title: Optional[str] = None,
    ) -> None:
        """Сохраняет запись об операции поиска/суммаризации."""
        await self.connection.execute(
            """
            INSERT INTO search_history
                (channel_id, channel_title, search_date, query, action_type, result_summary, messages_count, topic_id, topic_title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (channel_id, channel_title, search_date, query, action_type, result_summary, messages_count, topic_id, topic_title),
        )
        await self.connection.commit()

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Получает значение настройки."""
        cursor = await self.connection.execute(
            "SELECT value FROM user_settings WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        """Устанавливает значение настройки."""
        await self.connection.execute(
            """
            INSERT INTO user_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        await self.connection.commit()

    async def close(self) -> None:
        """Закрывает соединение с БД."""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с БД закрыто")
