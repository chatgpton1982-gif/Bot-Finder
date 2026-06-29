"""Обработчик настроек — выбор AI-провайдера и управление API-ключами."""

import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.main import get_main_keyboard
from bot.keyboards.settings import get_providers_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Словарь доступных провайдеров
AI_PROVIDERS = {
    "openai": "OpenAI (GPT-4o-mini)",
    "gemini": "Google Gemini",
    "anthropic": "Anthropic Claude",
    "deepseek": "DeepSeek",
    "openrouter": "OpenRouter (free)",
    "custom": "Кастомный (OpenAI-совместимый)",
    "ollama": "Ollama (локальный)",
}


class SettingsStates(StatesGroup):
    """Состояния FSM для настроек."""
    select_provider = State()
    enter_api_key = State()


@router.callback_query(F.data == "action_settings")
async def settings_start(
    callback: types.CallbackQuery,
    db=None,
) -> None:
    """Открыть меню настроек."""
    # Получаем текущий выбранный провайдер
    current_provider = await db.get_setting("ai_provider", "openai")
    provider_name = AI_PROVIDERS.get(current_provider, current_provider)

    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        f"Текущий провайдер: <b>{provider_name}</b>\n\n"
        "Выберите AI-провайдера для генерации сводок:",
        reply_markup=get_providers_keyboard(current_provider),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("provider:"))
async def select_provider(
    callback: types.CallbackQuery,
    state: FSMContext,
    db=None,
) -> None:
    """Обработка выбора провайдера и сохранение в БД."""
    provider = callback.data.split(":", 1)[1]
    provider_name = AI_PROVIDERS.get(provider, provider)

    # Сохраняем выбранный провайдер в БД
    await db.set_setting("ai_provider", provider)

    logger.info(f"Пользователь выбрал AI-провайдера: {provider}")

    await callback.message.edit_text(
        f"✅ Выбран провайдер: <b>{provider_name}</b>\n\n"
        "Для смены API-ключей обратитесь к файлу <code>.env</code>\n"
        "или настройте переменные окружения.\n\n"
        "Доступные провайдеры:\n"
        "• <b>OpenAI</b> — <code>OPENAI_API_KEY</code>\n"
        "• <b>Gemini</b> — <code>GEMINI_API_KEY</code>\n"
        "• <b>Anthropic</b> — <code>ANTHROPIC_API_KEY</code>\n"
        "• <b>DeepSeek</b> — <code>DEEPSEEK_API_KEY</code>\n"
        "• <b>OpenRouter</b> — <code>OPENROUTER_API_KEY</code>\n"
        "• <b>Кастомный</b> — <code>CUSTOM_API_BASE</code>, <code>CUSTOM_API_KEY</code>, <code>CUSTOM_MODEL</code>\n"
        "• <b>Ollama</b> — <code>OLLAMA_API_BASE</code>, <code>OLLAMA_MODEL</code>",
        reply_markup=get_main_keyboard(),
    )
    await callback.answer()
