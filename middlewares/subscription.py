"""Majburiy kanalga obunani tekshiruvchi middleware."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, ChatMember, Message, TelegramObject

import config
from database import Database
from keyboards import subscription_keyboard
from texts import SUBSCRIPTION_REQUIRED

logger = logging.getLogger(__name__)

SUB_CHECK_CALLBACK = "sub:check"


def _is_subscribed(member: ChatMember) -> bool:
    if member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    }:
        return True
    if member.status == ChatMemberStatus.RESTRICTED:
        return bool(getattr(member, "is_member", False))
    return False


async def get_missing_channels(bot: Any, user_id: int, channels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Foydalanuvchi obuna bo'lmagan kanallar ro'yxatini qaytaradi."""
    missing: list[dict[str, Any]] = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel["chat_id"], user_id)
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            # Bot kanalda emas yoki huquqi yetmaydi — foydalanuvchini bloklamaymiz.
            logger.warning("Kanalni tekshirib bo'lmadi (%s): %s", channel["chat_id"], exc)
            continue
        if not _is_subscribed(member):
            missing.append(channel)
    return missing


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")

        # Adminlar, botlar va «Tekshirish» tugmasi tekshiruvsiz o'tadi.
        if user is None or user.is_bot or user.id in config.ADMIN_IDS:
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == SUB_CHECK_CALLBACK:
            return await handler(event, data)

        channels = await self.db.get_channels()
        if not channels:
            return await handler(event, data)

        missing = await get_missing_channels(data["bot"], user.id, channels)
        if not missing:
            return await handler(event, data)

        markup = subscription_keyboard(missing)
        if isinstance(event, CallbackQuery):
            await event.answer("🔒 Avval kanallarga obuna bo'ling", show_alert=True)
            if isinstance(event.message, Message):
                await event.message.answer(SUBSCRIPTION_REQUIRED, reply_markup=markup)
        else:
            await event.answer(SUBSCRIPTION_REQUIRED, reply_markup=markup)
        return None
