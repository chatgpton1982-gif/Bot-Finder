"""Сервис для работы с AI-моделями через LiteLLM."""

import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMService:
    """
    Сервис для генерации сводок сообщений через различные AI-провайдеры.

    Поддерживаемые провайдеры: OpenAI, Gemini, Anthropic, DeepSeek, Ollama,
    OpenRouter, а также кастомные OpenAI-совместимые API (custom).
    Переключение между провайдерами осуществляется сменой модели.
    """

    # Маппинг провайдеров на модели LiteLLM
    PROVIDER_MODELS = {
        "openai": "gpt-4o-mini",
        "gemini": "gemini/gemini-2.0-flash",
        "anthropic": "claude-3-haiku-20240307",
        "deepseek": "deepseek/deepseek-chat",
        "ollama": "ollama/llama3",  # Будет заменено на config.ollama_model
        "openrouter": "openrouter/meta-llama/llama-3.2-3b-instruct:free",  # Бесплатная модель
        "custom": "custom",  # Кастомный OpenAI-совместимый API
    }

    def __init__(
        self,
        default_provider: str = "openai",
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        ollama_api_base: str = "http://localhost:11434",
        ollama_model: str = "llama3",
        custom_api_base: Optional[str] = None,
        custom_api_key: Optional[str] = None,
        custom_model: str = "mimo-v2-flash",
    ) -> None:
        self.default_provider = default_provider

        # Сохраняем API-ключи
        self._api_keys = {
            "openai": openai_api_key,
            "gemini": gemini_api_key,
            "anthropic": anthropic_api_key,
            "deepseek": deepseek_api_key,
            "openrouter": openrouter_api_key,
            "custom": custom_api_key,
        }

        self._ollama_api_base = ollama_api_base
        self._ollama_model = ollama_model

        # Параметры кастомного провайдера
        self._custom_api_base = custom_api_base
        self._custom_model = custom_model

        # Устанавливаем API-ключи в окружение для LiteLLM
        self._set_api_keys()

    def _set_api_keys(self) -> None:
        """Устанавливает API-ключи в переменные окружения для LiteLLM."""
        import os

        if self._api_keys["openai"]:
            os.environ["OPENAI_API_KEY"] = self._api_keys["openai"]
        if self._api_keys["gemini"]:
            os.environ["GEMINI_API_KEY"] = self._api_keys["gemini"]
        if self._api_keys["anthropic"]:
            os.environ["ANTHROPIC_API_KEY"] = self._api_keys["anthropic"]
        if self._api_keys["deepseek"]:
            os.environ["DEEPSEEK_API_KEY"] = self._api_keys["deepseek"]
        if self._api_keys["openrouter"]:
            os.environ["OPENROUTER_API_KEY"] = self._api_keys["openrouter"]
        if self._api_keys["custom"]:
            os.environ["CUSTOM_API_KEY"] = self._api_keys["custom"]
        if self._ollama_api_base:
            os.environ["OLLAMA_API_BASE"] = self._ollama_api_base

    def _get_model(self, provider: Optional[str] = None) -> str:
        """Возвращает модель для указанного провайдера."""
        provider = provider or self.default_provider
        model = self.PROVIDER_MODELS.get(provider, self.PROVIDER_MODELS["openai"])

        # Для Ollama подставляем конкретную модель
        if provider == "ollama":
            model = f"ollama/{self._ollama_model}"

        # Для кастомного провайдера — используем название модели из конфига
        # Добавляем префикс openai/, чтобы LiteLLM знал, что это OpenAI-совместимый API
        if provider == "custom":
            model = f"openai/{self._custom_model}"

        return model

    async def summarize(
        self,
        text: str,
        channel_name: str,
        date: datetime.date,
        provider: Optional[str] = None,
    ) -> str:
        """
        Генерирует краткую сводку переписки за указанную дату.

        Параметры:
            text: Текст всех сообщений за день
            channel_name: Название канала
            date: Дата
            provider: Провайдер AI (если None — используется default_provider)

        Returns:
            Строка со сводкой
        """
        model = self._get_model(provider)

        system_prompt = (
            "Ты — ассистент для анализа Telegram-каналов. "
            "Твоя задача — сделать краткую, информативную сводку сообщений за день. "
            "Выдели основные темы, ключевые обсуждения и важные моменты. "
            "Ответ дай на русском языке, структурированно."
        )

        user_prompt = (
            f"Канал: {channel_name}\n"
            f"Дата: {date.strftime('%d.%m.%Y')}\n\n"
            f"Сообщения за день:\n{text}\n\n"
            "Сделай краткую сводку (3-5 предложений) о чём была переписка. "
            "Выдели основные темы."
        )

        try:
            import litellm

            # Базовые параметры запроса
            kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            }

            # Для кастомного провайдера передаём api_base и api_key
            provider = provider or self.default_provider
            if provider == "custom" and self._custom_api_base:
                kwargs["api_base"] = self._custom_api_base
                if self._api_keys.get("custom"):
                    kwargs["api_key"] = self._api_keys["custom"]

            response = await litellm.acompletion(**kwargs)

            summary = response.choices[0].message.content.strip()
            logger.info(f"Сводка сгенерирована через {model} ({len(text)} символов текста)")
            return summary

        except Exception as e:
            logger.exception(f"Ошибка при генерации сводки через {model}")
            raise RuntimeError(f"Ошибка AI-провайдера {model}: {e}")
