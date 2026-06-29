import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Конфигурация приложения, загружаемая из .env файла."""

    # Telegram Bot
    bot_token: str

    # Telethon (личный аккаунт)
    api_id: int
    api_hash: str
    phone_number: str

    # AI провайдер по умолчанию
    default_ai_provider: str = "openai"

    # OpenAI
    openai_api_key: Optional[str] = None

    # Google Gemini
    gemini_api_key: Optional[str] = None

    # Anthropic Claude
    anthropic_api_key: Optional[str] = None

    # DeepSeek
    deepseek_api_key: Optional[str] = None

    # OpenRouter (бесплатные модели)
    openrouter_api_key: Optional[str] = None

    # Ollama (локальный)
    ollama_api_base: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Кастомный OpenAI-совместимый провайдер (например Xiaomi MiMo, OpenRouter и др.)
    custom_api_base: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: str = "mimo-v2-flash"

    # База данных
    database_path: str = "data/bot_database.sqlite"

    # Ограничение доступа (список user_id через запятую, пусто = всем)
    allowed_user_ids: list = field(default_factory=list)


def load_config() -> Config:
    """Загружает конфигурацию из .env файла."""
    load_dotenv()

    return Config(
        bot_token=_require_env("BOT_TOKEN"),
        api_id=int(_require_env("API_ID")),
        api_hash=_require_env("API_HASH"),
        phone_number=_require_env("PHONE_NUMBER"),
        default_ai_provider=os.getenv("DEFAULT_AI_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        ollama_api_base=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
        custom_api_base=os.getenv("CUSTOM_API_BASE"),
        custom_api_key=os.getenv("CUSTOM_API_KEY"),
        custom_model=os.getenv("CUSTOM_MODEL", "mimo-v2-flash"),
        database_path=os.getenv("DATABASE_PATH", "data/bot_database.sqlite"),
        allowed_user_ids=_parse_user_ids(os.getenv("ALLOWED_USER_IDS", "")),
    )


def _parse_user_ids(raw: str) -> list:
    """Парсит ALLOWED_USER_IDS из строки '123,456,789' в список int."""
    if not raw or not raw.strip():
        return []
    return [int(uid.strip()) for uid in raw.split(",") if uid.strip().isdigit()]


def _require_env(name: str) -> str:
    """Возвращает значение переменной окружения или вызывает ошибку."""
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"Переменная окружения {name} не установлена. "
            f"Скопируйте .env.example в .env и заполните значения."
        )
    return value
