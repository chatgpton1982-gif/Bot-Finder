"""Клавиатура для выбора AI-провайдера в настройках."""

from typing import Optional

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Словарь доступных провайдеров
AI_PROVIDERS = {
    "openai": "🤖 OpenAI (GPT-4o-mini)",
    "gemini": "🧠 Google Gemini",
    "anthropic": "📝 Anthropic Claude",
    "deepseek": "🔮 DeepSeek",
    "openrouter": "🌐 OpenRouter (free)",
    "custom": "⚙️ Кастомный (OpenAI-совместимый)",
    "ollama": "🖥️ Ollama (локально)",
}


def get_providers_keyboard(
    current_provider: Optional[str] = None,
) -> types.InlineKeyboardMarkup:
    """
    Создаёт клавиатуру со списком AI-провайдеров.

    Параметры:
        current_provider: Текущий выбранный провайдер (будет отмечен галочкой)

    Returns:
        InlineKeyboardMarkup с кнопками провайдеров
    """
    builder = InlineKeyboardBuilder()

    for provider_id, provider_name in AI_PROVIDERS.items():
        # Отмечаем текущий провайдер галочкой
        if provider_id == current_provider:
            display_name = f"✅ {provider_name}"
        else:
            display_name = provider_name
        builder.button(text=display_name, callback_data=f"provider:{provider_id}")

    builder.adjust(1)
    return builder.as_markup()
