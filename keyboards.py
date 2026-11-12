"""Inline klaviaturalar (chiroyli tugmalar)."""

from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from translator import LANGUAGES
from utils import shorten


def languages_keyboard(text_id: int) -> InlineKeyboardMarkup:
    """5 til tugmasi + yopish."""
    builder = InlineKeyboardBuilder()
    for code, info in LANGUAGES.items():
        builder.button(
            text=f"{info['flag']} {info['native']}",
            callback_data=f"tr:{text_id}:{code}",
        )
    builder.button(text="🧹 Yopish", callback_data="tr:close:close")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def channel_url(channel: dict[str, Any]) -> str | None:
    if channel.get("invite_link"):
        return str(channel["invite_link"])
    if channel.get("username"):
        return f"https://t.me/{channel['username']}"
    chat_id = channel.get("chat_id")
    if chat_id:
        internal = str(chat_id).replace("-100", "", 1)
        return f"https://t.me/c/{internal}"
    return None


def subscription_keyboard(channels: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Obuna bo'lish tugmalari va «Tekshirish»."""
    builder = InlineKeyboardBuilder()
    for channel in channels:
        url = channel_url(channel)
        if url:
            builder.button(text=f"📢 {shorten(str(channel.get('title') or 'Kanal'), 32)}", url=url)
    builder.button(text="✅ Tekshirish", callback_data="sub:check")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu_keyboard(channels_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 E'lon yuborish", callback_data="admin:broadcast")
    builder.button(text="📣 Reklama yuborish", callback_data="admin:ad")
    builder.button(
        text=f"📌 Majburiy kanallar ({channels_count})",
        callback_data="admin:channels",
    )
    builder.button(text="📊 Statistika", callback_data="admin:stats")
    builder.button(text="🧹 Yopish", callback_data="admin:close")
    builder.adjust(1)
    return builder.as_markup()


def admin_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Admin panel", callback_data="admin:menu")
    builder.button(text="🧹 Yopish", callback_data="admin:close")
    builder.adjust(2)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    builder.adjust(1)
    return builder.as_markup()


def channels_keyboard(channels: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        title = shorten(str(channel.get("title") or "Kanal"), 28)
        builder.button(text=f"🗑 {title}", callback_data=f"admin:delch:{channel['chat_id']}")
    builder.button(text="➕ Kanal qo'shish", callback_data="admin:addchannel")
    builder.button(text="⬅️ Admin panel", callback_data="admin:menu")
    builder.button(text="🧹 Yopish", callback_data="admin:close")
    builder.adjust(1)
    return builder.as_markup()
