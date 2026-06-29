"""Обработчик команды /start и главное меню."""

from aiogram import Router, types
from aiogram.filters import CommandStart

from bot.keyboards.main import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """Обработчик команды /start — показывает главное меню."""
    await message.answer(
        "👋 <b>Привет! Я бот для поиска и анализа сообщений в Telegram каналах.</b>\n\n"
        "Я могу:\n"
        "🔍 <b>Искать</b> сообщения по ключевым словам за определённую дату\n"
        "📊 <b>Суммаризировать</b> переписку за день\n\n"
        "Используй кнопки ниже, чтобы начать.",
        reply_markup=get_main_keyboard(),
    )
