"""Kichik yordamchi funksiyalar."""

from __future__ import annotations

import html

from aiogram.types import CallbackQuery, Message


def callback_message(callback: CallbackQuery) -> Message | None:
    """Callback xabari tahrirlash mumkin bo'lsa qaytaradi (eski xabarlar uchun None)."""
    message = callback.message
    return message if isinstance(message, Message) else None


def escape(value: str | None) -> str:
    """Foydalanuvchi matnini HTML uchun xavfsiz qiladi."""
    return html.escape(value or "", quote=False)


def shorten(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def html_split(text: str, limit: int = 3000) -> list[str]:
    """Matnni HTML-xavfsiz qismlarga bo'ladi.

    Bo'lish paytida HTML entitylar (&amp;, &lt; va h.k.) va
    qatorlar butunligicha saqlanadi.
    """
    escaped = html.escape(text or "", quote=False)
    chunks: list[str] = []
    start = 0
    total = len(escaped)

    while start < total:
        end = min(start + limit, total)
        if end < total:
            amp = escaped.rfind("&", start, end)
            if amp != -1 and escaped.find(";", amp, end) == -1:
                end = amp
            newline = escaped.rfind("\n", start, end)
            if newline > start + limit // 2:
                end = newline
            else:
                space = escaped.rfind(" ", start, end)
                if space > start + limit // 2:
                    end = space
        if end <= start:
            end = min(start + limit, total)
        chunk = escaped[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end

    return chunks or [""]
