"""Formatting search results and summaries for sending to user."""

import datetime
from typing import List, Optional

from telethon.tl.types import Message


def format_search_results(
    messages: List[Message],
    channel_id: int,
    date: datetime.date,
    query: str,
    max_preview: int = 200,
    max_results: int = 20,
) -> str:
    """
    Format search results for sending to user.

    Args:
        messages: List of found messages
        channel_id: Channel ID
        date: Search date
        query: Search query
        max_preview: Max preview text length
        max_results: Max messages in output

    Returns:
        Formatted text with results
    """
    result_parts = []
    for msg in messages[:max_results]:
        link = _build_message_link(channel_id, msg.id)
        date_str = msg.date.strftime("%H:%M") if msg.date else "??:??"
        text_preview = (msg.text or "[Media]")[:max_preview]
        result_parts.append(
            f"\u2022 <a href='{link}'>[{date_str}]</a> {_escape_html(text_preview)}"
        )

    response = (
        "\U0001f50d <b>Results</b>\n"
        f"\U0001f4c5 Date: {date.strftime('%d.%m.%Y')}\n"
        f"\U0001f50e Query: \u00ab{_escape_html(query)}\u00bb\n"
        f"\U0001f4ca Found: {len(messages)} messages\n\n"
        + "\n".join(result_parts)
    )

    if len(messages) > max_results:
        response += f"\n\n<i>...and {len(messages) - max_results} more messages.</i>"

    return response


def format_summary_result(
    summary: str,
    channel_name: str,
    date: datetime.date,
    messages_count: int,
    text_count: int,
) -> str:
    """
    Format summary result for sending to user.

    Args:
        summary: AI summary text
        channel_name: Channel name
        date: Date
        messages_count: Total messages count
        text_count: Text messages count

    Returns:
        Formatted summary text
    """
    return (
        "\U0001f4ca <b>Summary for {}</b>\n"
        "\U0001f4e2 Channel: {}\n"
        "\U0001f4ca Total messages: {}\n"
        "\U0001f4dd With text: {}\n\n"
        "{}"
    ).format(
        date.strftime("%d.%m.%Y"),
        _escape_html(channel_name),
        messages_count,
        text_count,
        summary,
    )


def format_no_results(date: datetime.date, query: Optional[str] = None) -> str:
    """
    Format no results message.

    Args:
        date: Search date
        query: Search query (if None - no messages for date at all)

    Returns:
        No results text
    """
    date_str = date.strftime("%d.%m.%Y")
    if query:
        return (
            "\u274c No messages for query \u00ab{}\u00bb "
            "on {}."
        ).format(_escape_html(query), date_str)
    return "\u274c No messages on {} in this channel.".format(date_str)


def format_error(message: str) -> str:
    """
    Format error message.

    Args:
        message: Error text

    Returns:
        Formatted error message
    """
    return "\u26a0\ufe0f <b>Error:</b>\n{}".format(_escape_html(message))


def format_loading_status(action: str, detail: Optional[str] = None) -> str:
    """
    Format loading/processing status.

    Args:
        action: Action type ("search", "summary", "fetch")
        detail: Additional info

    Returns:
        Status text
    """
    statuses = {
        "search": "\u23f3 Searching messages",
        "summary": "\U0001f916 Generating summary",
        "fetch": "\u23f3 Fetching messages",
    }
    base = statuses.get(action, "\u23f3 Processing")
    if detail:
        return "{} {}...".format(base, detail)
    return "{}...".format(base)


def _build_message_link(channel_id: int, message_id: int) -> str:
    """
    Build a link to a Telegram message.

    Args:
        channel_id: Channel ID
        message_id: Message ID

    Returns:
        Message URL
    """
    str_id = str(channel_id)
    if str_id.startswith("-100"):
        str_id = str_id[4:]
    return "https://t.me/c/{}/{}".format(str_id, message_id)


def _escape_html(text: str) -> str:
    """Escape HTML special characters for safe display."""
    AMP = chr(38) + "amp;"
    LT = chr(38) + "lt;"
    GT = chr(38) + "gt;"
    QUOT = chr(38) + "quot;"
    text = text.replace(chr(38), AMP)
    text = text.replace(chr(60), LT)
    text = text.replace(chr(62), GT)
    text = text.replace(chr(34), QUOT)
    return text
