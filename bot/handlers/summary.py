"""Обработчик суммаризации сообщений за дату."""

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


class SummaryStates(StatesGroup):
    """Состояния FSM для процесса суммаризации."""
    select_channel = State()
    select_topic = State()
    select_date = State()


@router.callback_query(F.data == "action_summary")
async def summary_start(
    callback: types.CallbackQuery,
    state: FSMContext,
    telegram_client=None,
) -> None:
    """Начало суммаризации — выбор канала."""
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
        "📋 <b>Выберите канал для сводки:</b>",
        reply_markup=get_channels_keyboard(channels),
    )
    await state.set_state(SummaryStates.select_channel)


@router.callback_query(StateFilter(SummaryStates.select_channel), F.data.startswith("channel:"))
async def summary_select_channel(
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
            "📋 <b>Выберите чат (топик) для сводки:</b>\n\n"
            "Или выберите «Весь канал», чтобы сделать сводку по всем сообщениям.",
            reply_markup=get_topics_keyboard(topics, channel_id),
        )
        await state.set_state(SummaryStates.select_topic)
    else:
        # Если топиков нет — сразу переходим к выбору даты
        await callback.message.edit_text(
            "📅 <b>Выберите дату для сводки:</b>",
            reply_markup=get_calendar_keyboard(),
        )
        await state.set_state(SummaryStates.select_date)

    await callback.answer()


@router.callback_query(StateFilter(SummaryStates.select_topic), F.data.startswith("topic:"))
async def summary_select_topic(callback: types.CallbackQuery, state: FSMContext) -> None:
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
        # Получаем название топика из callback_data (не передаётся, сохраним позже)
        await state.update_data(topic_id=topic_id, topic_title=None)

    await callback.message.edit_text(
        "📅 <b>Выберите дату для сводки:</b>",
        reply_markup=get_calendar_keyboard(),
    )
    await state.set_state(SummaryStates.select_date)
    await callback.answer()


@router.callback_query(
    StateFilter(SummaryStates.select_date),
    CalendarCallbackData.filter(),
)
async def summary_handle_calendar(
    callback: types.CallbackQuery,
    state: FSMContext,
    callback_data: CalendarCallbackData,
    telegram_client=None,
    llm_service=None,
    db=None,
) -> None:
    """Обрабатывает выбор даты и запускает генерацию сводки."""
    if callback_data.action in ("prev_month", "next_month"):
        # Навигация по месяцам
        await callback.message.edit_text(
            "📅 <b>Выберите дату для сводки:</b>",
            reply_markup=get_calendar_keyboard(callback_data.year, callback_data.month),
        )
        await callback.answer()
        return

    # action == "select" — пользователь выбрал дату
    selected_date = datetime.date(callback_data.year, callback_data.month, callback_data.day)
    data = await state.get_data()
    channel_id = data["channel_id"]
    topic_id = data.get("topic_id")
    topic_title = data.get("topic_title")

    # Формируем сообщение о статусе
    topic_info = f" в чате «{topic_title}»" if topic_id and topic_title else ""
    await callback.message.edit_text(
        f"⏳ Получаю сообщения за {selected_date.strftime('%d.%m.%Y')}{topic_info}..."
    )

    try:
        messages = await telegram_client.get_messages(
            channel_id=channel_id,
            date=selected_date,
            topic_id=topic_id,
        )

    except (ConnectionError, TimeoutError):
        logger.error(f"Telethon: нет соединения при получении сообщений канала {channel_id}")
        await callback.message.edit_text(
            "🔌 <b>Потеряно соединение с Telegram.</b>\n"
            "Попробуйте позже или начните заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    except Exception as e:
        error_type = type(e).__name__
        logger.exception(f"Ошибка Telethon при получении сообщений: {error_type}")

        if "ChatAdminRequired" in error_type or "ChannelPrivate" in error_type:
            await callback.message.edit_text(
                "🔒 <b>Канал недоступен.</b>\n\n"
                "У вас нет прав для чтения сообщений в этом канале.\n"
                "Обновите список каналов и попробуйте другой.",
                reply_markup=get_main_keyboard(),
            )
        elif "FloodWait" in error_type:
            wait_time = getattr(e, "seconds", 60)
            minutes = wait_time // 60
            await callback.message.edit_text(
                f"🚦 <b>Слишком много запросов.</b>\n\n"
                f"Telegram просит подождать ~{minutes} мин.\n"
                f"Попробуйте позже.",
                reply_markup=get_main_keyboard(),
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Произошла ошибка при получении сообщений.</b>\n\n"
                f"<i>Тип ошибки: {error_type}</i>\n\n"
                "Попробуйте позже или выберите другой канал.",
                reply_markup=get_main_keyboard(),
            )

        await state.clear()
        await callback.answer()
        return

    if not messages:
        msg = f"❌ За {selected_date.strftime('%d.%m.%Y')}"
        if topic_id and topic_title:
            msg += f" в чате «{topic_title}»"
        msg += " сообщений не найдено."
        await callback.message.edit_text(
            msg,
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    # Показываем статус генерации сводки
    msg_count = len(messages)
    text_count = sum(1 for m in messages if m.text)
    await callback.message.edit_text(
        f"📊 Найдено {msg_count} сообщений (из них {text_count} с текстом).\n"
        f"🤖 Генерирую сводку... Это может занять несколько секунд."
    )

    # Собираем текст всех сообщений
    all_text = "\n\n".join(
        f"[{msg.date.strftime('%H:%M') if msg.date else '??:??'}] "
        f"{msg.text or '[Медиа]'}"
        for msg in messages if msg.text
    )

    # Получаем название канала из первого сообщения
    channel_name = messages[0].chat.title if messages[0].chat else "Канал"

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

    # Формируем название для сводки (канал + топик)
    summary_channel_name = channel_name
    if topic_title:
        summary_channel_name = f"{channel_name} / {topic_title}"

    # Вызываем LLM для генерации сводки
    try:
        summary = await llm_service.summarize(
            text=all_text,
            channel_name=summary_channel_name,
            date=selected_date,
        )
    except Exception as e:
        error_type = type(e).__name__
        logger.exception(f"Ошибка LLM при генерации сводки: {error_type}")

        if "AuthenticationError" in error_type or "PermissionDenied" in error_type:
            await callback.message.edit_text(
                "🔑 <b>Ошибка авторизации AI-провайдера.</b>\n\n"
                "Проверьте API-ключ в настройках (/settings).\n"
                "Или выберите другой провайдер.",
                reply_markup=get_main_keyboard(),
            )
        elif "RateLimitError" in error_type or "429" in str(e):
            await callback.message.edit_text(
                "🚦 <b>AI-провайдер перегружен.</b>\n\n"
                "Превышен лимит запросов. Попробуйте позже\n"
                "или выберите другой провайдер в /settings.",
                reply_markup=get_main_keyboard(),
            )
        elif "APIConnectionError" in error_type or "Timeout" in error_type:
            await callback.message.edit_text(
                "🔌 <b>AI-провайдер недоступен.</b>\n\n"
                "Не удалось подключиться к сервису AI.\n"
                "Попробуйте позже или выберите другой провайдер в /settings.",
                reply_markup=get_main_keyboard(),
            )
        else:
            await callback.message.edit_text(
                f"⚠️ <b>Ошибка при генерации сводки.</b>\n\n"
                f"<i>Тип ошибки: {error_type}</i>\n\n"
                "Попробуйте позже или выберите другой провайдер в /settings.",
                reply_markup=get_main_keyboard(),
            )

        await state.clear()
        await callback.answer()
        return

    # Формируем ответ
    response_parts = [
        f"📊 <b>Сводка за {selected_date.strftime('%d.%m.%Y')}</b>",
        f"📢 Канал: {channel_name}",
    ]
    if topic_title:
        response_parts.append(f"💬 Чат: {topic_title}")
    response_parts.append(f"📊 Всего сообщений: {msg_count}")
    response_parts.append(f"📝 С текстом: {text_count}")
    response_parts.append("")
    response_parts.append(summary)

    response = "\n".join(response_parts)

    await callback.message.edit_text(
        response,
        reply_markup=get_main_keyboard(),
    )

    # Сохраняем в историю
    try:
        await db.save_search_history(
            channel_id=channel_id,
            channel_title=channel_name,
            search_date=selected_date.isoformat(),
            query="",
            action_type="summary",
            result_summary=summary,
            messages_count=msg_count,
            topic_id=topic_id,
            topic_title=topic_title,
        )
    except Exception as e:
        logger.warning(f"Не удалось сохранить историю поиска: {e}")

    await state.clear()
    await callback.answer()
