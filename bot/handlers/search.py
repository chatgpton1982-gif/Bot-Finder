"""Обработчик поиска сообщений по ключевым словам."""

import datetime
import logging

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.channels import get_channels_keyboard
from bot.keyboards.topics import get_topics_keyboard
from bot.keyboards.calendar import CalendarCallbackData, get_calendar_keyboard
from bot.keyboards.main import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()


class SearchStates(StatesGroup):
    """Состояния FSM для процесса поиска."""
    select_channel = State()
    select_topic = State()
    select_date = State()
    enter_query = State()


@router.callback_query(F.data == "action_search")
async def search_start(
    callback: types.CallbackQuery,
    state: FSMContext,
    telegram_client=None,
) -> None:
    """Начало поиска — запрос выбора канала."""
    await callback.answer("⏳ Загружаю список каналов...", show_alert=False)

    try:
        channels = await telegram_client.get_dialogs()
    except ConnectionError:
        logger.error("Telethon: нет соединения при получении списка каналов")
        await callback.message.edit_text(
            "🔌 <b>Нет соединения с Telegram.</b>\n\n"
            "Попробуйте позже или перезапустите бота командой /start.",
            reply_markup=get_main_keyboard(),
        )
        return
    except Exception as e:
        logger.exception("Ошибка при получении списка каналов")
        await callback.message.edit_text(
            f"⚠️ Не удалось загрузить список каналов.\n\n"
            f"<i>Ошибка: {type(e).__name__}</i>",
            reply_markup=get_main_keyboard(),
        )
        return

    if not channels:
        await callback.message.edit_text(
            "📭 <b>Каналы не найдены.</b>\n\n"
            "Убедитесь, что вы состоите в каналах/группах, "
            "и попробуйте снова.",
            reply_markup=get_main_keyboard(),
        )
        return

    await callback.message.edit_text(
        "📋 <b>Выберите канал для поиска:</b>",
        reply_markup=get_channels_keyboard(channels),
    )
    await state.set_state(SearchStates.select_channel)


@router.callback_query(StateFilter(SearchStates.select_channel), F.data.startswith("channel:"))
async def search_select_channel(
    callback: types.CallbackQuery,
    state: FSMContext,
    telegram_client=None,
) -> None:
    """Выбор канала — проверяем наличие топиков форума."""
    channel_id = int(callback.data.split(":", 1)[1])
    await state.update_data(channel_id=channel_id)

    try:
        # Проверяем, есть ли у канала форум с топиками
        topics = await telegram_client.get_forum_topics(channel_id)
    except (ConnectionError, TimeoutError):
        await callback.message.edit_text(
            "🔌 <b>Нет соединения с Telegram.</b>\n"
            "Попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return
    except Exception as e:
        logger.exception(f"Ошибка при проверке топиков канала {channel_id}")
        await callback.message.edit_text(
            "⚠️ <b>Канал недоступен.</b>\n\n"
            "Возможно, канал был удалён или у вас нет к нему доступа.\n"
            "Попробуйте обновить список каналов.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    if topics:
        # Если есть топики — предлагаем выбрать
        await callback.message.edit_text(
            "📋 <b>Выберите чат (топик) для поиска:</b>\n\n"
            "Или выберите «Весь канал», чтобы искать по всем сообщениям.",
            reply_markup=get_topics_keyboard(topics, channel_id),
        )
        await state.set_state(SearchStates.select_topic)
    else:
        # Если топиков нет — сразу переходим к выбору даты
        await callback.message.edit_text(
            "📅 <b>Выберите дату для поиска:</b>",
            reply_markup=get_calendar_keyboard(),
        )
        await state.set_state(SearchStates.select_date)

    await callback.answer()


@router.callback_query(StateFilter(SearchStates.select_topic), F.data.startswith("topic:"))
async def search_select_topic(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Выбор топика — запрос даты."""
    parts = callback.data.split(":")
    channel_id = int(parts[1])
    topic_value = parts[2]

    if topic_value == "all":
        # Весь канал
        await state.update_data(topic_id=None, topic_title=None)
    else:
        # Конкретный топик
        topic_id = int(topic_value)
        await state.update_data(topic_id=topic_id, topic_title=None)

    await callback.message.edit_text(
        "📅 <b>Выберите дату для поиска:</b>",
        reply_markup=get_calendar_keyboard(),
    )
    await state.set_state(SearchStates.select_date)
    await callback.answer()


@router.callback_query(
    StateFilter(SearchStates.select_date),
    CalendarCallbackData.filter(),
)
async def search_handle_calendar(
    callback: types.CallbackQuery,
    state: FSMContext,
    callback_data: CalendarCallbackData,
) -> None:
    """Обрабатывает выбор даты и навигацию по месяцам в календаре."""
    if callback_data.action == "prev_month":
        # Переключаем на предыдущий месяц
        await callback.message.edit_text(
            "📅 <b>Выберите дату для поиска:</b>",
            reply_markup=get_calendar_keyboard(callback_data.year, callback_data.month),
        )
        await callback.answer()
        return

    if callback_data.action == "next_month":
        # Переключаем на следующий месяц
        await callback.message.edit_text(
            "📅 <b>Выберите дату для поиска:</b>",
            reply_markup=get_calendar_keyboard(callback_data.year, callback_data.month),
        )
        await callback.answer()
        return

    # action == "select" — пользователь выбрал дату
    selected_date = datetime.date(callback_data.year, callback_data.month, callback_data.day)
    await state.update_data(search_date=selected_date.isoformat())

    # Получаем данные о топике для отображения
    data = await state.get_data()
    topic_title = data.get("topic_title")

    topic_info = f" в чате «{topic_title}»" if topic_title else ""

    await callback.message.edit_text(
        f"📅 Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>{topic_info}\n\n"
        "✏️ <b>Введите ключевые слова или фразу для поиска:</b>\n"
        "Можно искать несколько слов через пробел.\n\n"
        "Или нажмите кнопку, чтобы вернуться в меню.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
            ]
        ),
    )
    await state.set_state(SearchStates.enter_query)
    await callback.answer()


@router.message(StateFilter(SearchStates.enter_query))
async def search_execute(
    message: types.Message,
    state: FSMContext,
    telegram_client=None,
    db=None,
) -> None:
    """Поиск сообщений по ключевым словам."""
    query = message.text.strip()
    if not query:
        await message.answer("⚠️ Пожалуйста, введите ключевые слова.")
        return

    data = await state.get_data()
    channel_id = data.get("channel_id")
    search_date_str = data.get("search_date")
    topic_id = data.get("topic_id")
    topic_title = data.get("topic_title")

    # Проверка完整性 данных FSM
    if not channel_id or not search_date_str:
        await message.answer(
            "⚠️ <b>Сессия устарела.</b>\n"
            "Пожалуйста, начните поиск заново из главного меню.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    search_date = datetime.date.fromisoformat(search_date_str)
    topic_info = f" в чате «{topic_title}»" if topic_id and topic_title else ""
    status_msg = await message.answer(
        f"⏳ Ищу сообщения по запросу «{query}»{topic_info}..."
    )

    try:
        results = await telegram_client.search_messages(
            channel_id=channel_id,
            date=search_date,
            query=query,
            topic_id=topic_id,
        )

    except (ConnectionError, TimeoutError):
        logger.error(f"Telethon: нет соединения при поиске в канале {channel_id}")
        await status_msg.edit_text(
            "🔌 <b>Потеряно соединение с Telegram.</b>\n"
            "Попробуйте позже или начните поиск заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    except Exception as e:
        error_type = type(e).__name__
        logger.exception(f"Ошибка Telethon при поиске: {error_type}")

        if "ChatAdminRequired" in error_type or "ChannelPrivate" in error_type:
            await status_msg.edit_text(
                "🔒 <b>Канал недоступен.</b>\n\n"
                "У вас нет прав для чтения сообщений в этом канале.\n"
                "Обновите список каналов и попробуйте другой.",
                reply_markup=get_main_keyboard(),
            )
        elif "FloodWait" in error_type:
            # Извлекаем время ожидания из ошибки
            wait_time = getattr(e, "seconds", 60)
            minutes = wait_time // 60
            await status_msg.edit_text(
                f"🚦 <b>Слишком много запросов.</b>\n\n"
                f"Telegram просит подождать ~{minutes} мин.\n"
                f"Попробуйте позже.",
                reply_markup=get_main_keyboard(),
            )
        else:
            await status_msg.edit_text(
                f"⚠️ <b>Произошла ошибка при поиске.</b>\n\n"
                f"<i>Тип ошибки: {error_type}</i>\n\n"
                "Попробуйте позже или выберите другой канал.",
                reply_markup=get_main_keyboard(),
            )

        await state.clear()
        return

    if not results:
        msg = (
            f"❌ Сообщений по запросу «{query}» за "
            f"{search_date.strftime('%d.%m.%Y')}"
        )
        if topic_id and topic_title:
            msg += f" в чате «{topic_title}»"
        msg += " не найдено."
        await status_msg.edit_text(
            msg,
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    # Если название топика не сохранено — пытаемся получить его
    if topic_id and not topic_title:
        try:
            topics = await telegram_client.get_forum_topics(channel_id)
            for t in topics:
                if t["id"] == topic_id:
                    topic_title = t["title"]
                    await state.update_data(topic_title=topic_title)
                    break
        except Exception:
            logger.warning(f"Не удалось получить топики канала {channel_id}")

    # Формируем ответ
    result_parts = []
    for msg in results[:20]:  # Ограничение на 20 сообщений
        link = f"https://t.me/c/{str(channel_id).replace('-100', '')}/{msg.id}"
        date_str = msg.date.strftime("%H:%M") if msg.date else "??:??"
        text_preview = (msg.text or "[Медиа]")[:200]
        result_parts.append(
            f"• <a href='{link}'>[{date_str}]</a> {text_preview}"
        )

    response_parts = [
        f"🔍 <b>Результаты поиска</b>",
        f"📅 Дата: {search_date.strftime('%d.%m.%Y')}",
    ]
    if topic_title:
        response_parts.append(f"💬 Чат: {topic_title}")
    response_parts.append(f"🔎 Запрос: «{query}»")
    response_parts.append(f"📊 Найдено: {len(results)} сообщений")
    response_parts.append("")
    response_parts.append("\n".join(result_parts))

    response = "\n".join(response_parts)

    # Если результатов больше 20 — показываем пагинацию
    if len(results) > 20:
        response += f"\n\n<i>...и ещё {len(results) - 20} сообщений.</i>"

    await status_msg.edit_text(
        response,
        disable_web_page_preview=True,
        reply_markup=get_main_keyboard(),
    )

    # Сохраняем в историю
    try:
        await db.save_search_history(
            channel_id=channel_id,
            channel_title=results[0].chat.title if results[0].chat else "Канал",
            search_date=search_date.isoformat(),
            query=query,
            action_type="search",
            messages_count=len(results),
            topic_id=topic_id,
            topic_title=topic_title,
        )
    except Exception as e:
        logger.warning(f"Не удалось сохранить историю поиска: {e}")

    await state.clear()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(
        "🔙 Возвращаюсь в главное меню.",
        reply_markup=get_main_keyboard(),
    )
    await callback.answer()
