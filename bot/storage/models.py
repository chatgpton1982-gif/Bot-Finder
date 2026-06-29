"""Pydantic/dataclass модели для работы с данными."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CachedChannel:
    """Информация о канале из кэша."""
    channel_id: int
    title: str
    username: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class SearchHistoryEntry:
    """Запись истории поиска."""
    id: int
    channel_id: int
    channel_title: str
    search_date: str
    query: str
    action_type: str  # "search" или "summary"
    result_summary: str = ""
    messages_count: int = 0
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ChannelInfo:
    """Информация о канале для отображения пользователю."""
    id: int
    title: str
    username: Optional[str] = None


@dataclass
class TopicInfo:
    """Информация о топике (теме форума) для отображения пользователю."""
    id: int
    title: str
