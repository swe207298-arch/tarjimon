"""Admin panel: e'lon, reklama va majburiy kanallarni boshqarish."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    MessageOriginChannel,
)

import config
from database import Database
from keyboards import (
    admin_back_keyboard,
    admin_menu_keyboard,
    cancel_keyboard,
    channels_keyboard,
)
from texts import (
    AD_BUTTON_INVALID,
    AD_BUTTON_PROMPT,
    AD_PROMPT,
    ADD_CHANNEL_PROMPT,
    ADMIN_CHANNELS_EMPTY,
    ADMIN_CHANNELS_HINT,
    ADMIN_CHANNELS_TITLE,
    ADMIN_MENU,
    ADMIN_STATS,
    BROADCAST_DONE,
    BROADCAST_PROMPT,
    CHANNEL_ADDED,
    CHANNEL_BOT_NOT_ADMIN,
    CHANNEL_CHECK_FAILED,
    CHANNEL_NO_LINK,
    CHANNEL_NOT_CHANNEL,
    CHANNEL_NOT_FOUND,
)
from utils import callback_message, escape

logger = logging.getLogger(__name__)

router = Router(name="admin")
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return bool(user and user.id in config.ADMIN_IDS)


class AdminFlow(StatesGroup):
    broadcast = State()
    ad_content = State()
    ad_button = State()
    channel = State()


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ------------------------------------------------------------------ yordamchi


async def _menu_view(db: Database) -> tuple[str, InlineKeyboardMarkup]:
    users = await db.count_users()
    channels = await db.get_channels()
    text = ADMIN_MENU.format(users=users, channels=len(channels))
    return text, admin_menu_keyboard(len(channels))


async def _safe_edit(
    message: Message,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
) -> None:
    try:
        await message.edit_text(text, reply_markup=markup, link_preview_options=NO_PREVIEW)
    except TelegramAPIError:
        pass


async def _broadcast(
    bot: Bot,
    users: list[int],
    from_chat_id: int,
    message_id: int,
    reply_markup: InlineKeyboardMarkup | None = None,
    progress: Message | None = None,
) -> tuple[int, int]:
    """Xabarni barcha foydalanuvchilarga yuboradi. (yuborildi, xato)."""
    sent = failed = 0
    total = len(users)

    async def copy_once(user_id: int) -> None:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )

    for index, user_id in enumerate(users, 1):
        try:
            await copy_once(user_id)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
            try:
                await copy_once(user_id)
                sent += 1
            except TelegramAPIError as retry_exc:
                failed += 1
                logger.info("Xabar yuborilmadi (%s): %s", user_id, retry_exc)
        except TelegramAPIError as exc:
            failed += 1
            logger.info("Xabar yuborilmadi (%s): %s", user_id, exc)

        if progress and index % 25 == 0 and index < total:
            with contextlib.suppress(TelegramAPIError):
                await progress.edit_text(f"⏳ <b>Yuborilmoqda...</b>\n{index} / {total}")

        await asyncio.sleep(config.BROADCAST_DELAY)

    return sent, failed


# --------------------------------------------------------------------- menyu


@router.message(Command("admin"))
async def open_admin(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    text, markup = await _menu_view(db)
    await message.answer(text, reply_markup=markup, link_preview_options=NO_PREVIEW)


@router.callback_query(F.data == "admin:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    text, markup = await _menu_view(db)
    await callback.answer()
    message = callback_message(callback)
    if message:
        await _safe_edit(message, text, markup)


@router.callback_query(F.data == "admin:cancel")
async def cancel_flow(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    text, markup = await _menu_view(db)
    await callback.answer("Bekor qilindi")
    message = callback_message(callback)
    if message:
        await _safe_edit(message, "❌ <b>Amal bekor qilindi.</b>\n\n" + text, markup)


@router.message(Command("bekor"))
async def cancel_command(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    text, markup = await _menu_view(db)
    await message.answer(
        "❌ <b>Amal bekor qilindi.</b>\n\n" + text,
        reply_markup=markup,
        link_preview_options=NO_PREVIEW,
    )


@router.callback_query(F.data == "admin:close")
async def close_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    message = callback_message(callback)
    if message:
        with contextlib.suppress(TelegramAPIError):
            await message.delete()


# --------------------------------------------------------------- e'lon (broadcast)


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFlow.broadcast)
    await callback.answer()
    message = callback_message(callback)
    if message:
        await message.answer(BROADCAST_PROMPT, reply_markup=cancel_keyboard())


@router.message(AdminFlow.broadcast)
async def broadcast_send(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    await state.clear()
    users = await db.all_user_ids()
    if not users:
        await message.answer(
            "👥 Hozircha foydalanuvchilar yo'q.",
            reply_markup=admin_back_keyboard(),
        )
        return

    status = await message.answer(f"⏳ <b>Yuborilmoqda...</b>\n0 / {len(users)}")
    sent, failed = await _broadcast(
        bot,
        users,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        progress=status,
    )
    report = BROADCAST_DONE.format(sent=sent, failed=failed, total=len(users))
    await _safe_edit(status, report, admin_back_keyboard())


# --------------------------------------------------------------------- reklama


@router.callback_query(F.data == "admin:ad")
async def ad_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFlow.ad_content)
    await callback.answer()
    message = callback_message(callback)
    if message:
        await message.answer(AD_PROMPT, reply_markup=cancel_keyboard())


@router.message(AdminFlow.ad_content)
async def ad_content(message: Message, state: FSMContext) -> None:
    await state.update_data(ad_chat_id=message.chat.id, ad_message_id=message.message_id)
    await state.set_state(AdminFlow.ad_button)
    await message.answer(AD_BUTTON_PROMPT)


@router.message(AdminFlow.ad_button)
async def ad_send(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    raw = (message.text or "").strip()

    keyboard: InlineKeyboardMarkup | None = None
    if raw.lower() not in {"/skip", "skip", "-"}:
        if "|" not in raw:
            await message.answer(AD_BUTTON_INVALID)
            return
        label, url = (piece.strip() for piece in raw.split("|", 1))
        if not label or not url.startswith(("https://", "http://", "tg://")):
            await message.answer(AD_BUTTON_INVALID)
            return
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=label[:64], url=url)]]
        )

    data = await state.get_data()
    await state.clear()

    ad_chat_id = data.get("ad_chat_id")
    ad_message_id = data.get("ad_message_id")
    if not ad_chat_id or not ad_message_id:
        await message.answer("❌ Reklama kontenti topilmadi. Qaytadan boshlang.")
        return

    users = await db.all_user_ids()
    if not users:
        await message.answer(
            "👥 Hozircha foydalanuvchilar yo'q.",
            reply_markup=admin_back_keyboard(),
        )
        return

    status = await message.answer(f"⏳ <b>Reklama yuborilmoqda...</b>\n0 / {len(users)}")
    sent, failed = await _broadcast(
        bot,
        users,
        from_chat_id=int(ad_chat_id),
        message_id=int(ad_message_id),
        reply_markup=keyboard,
        progress=status,
    )
    report = BROADCAST_DONE.format(sent=sent, failed=failed, total=len(users))
    await _safe_edit(status, report, admin_back_keyboard())


# ------------------------------------------------------- majburiy kanallar


async def _render_channels(message: Message, db: Database, edit: bool = True) -> None:
    channels = await db.get_channels()
    lines = [ADMIN_CHANNELS_TITLE.format(count=len(channels))]
    if channels:
        for index, channel in enumerate(channels, 1):
            username = f"@{channel['username']}" if channel.get("username") else "yopiq kanal"
            title = escape(str(channel.get("title") or "Kanal"))
            lines.append(f"{index}. <b>{title}</b> — {escape(username)}")
    else:
        lines.append(ADMIN_CHANNELS_EMPTY)
    lines.append(ADMIN_CHANNELS_HINT)

    text = "\n".join(lines)
    markup = channels_keyboard(channels)
    if edit:
        await _safe_edit(message, text, markup)
    else:
        await message.answer(text, reply_markup=markup, link_preview_options=NO_PREVIEW)


@router.callback_query(F.data == "admin:channels")
async def show_channels(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    await callback.answer()
    message = callback_message(callback)
    if message:
        await _render_channels(message, db, edit=True)


@router.callback_query(F.data == "admin:addchannel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFlow.channel)
    await callback.answer()
    message = callback_message(callback)
    if message:
        await message.answer(ADD_CHANNEL_PROMPT, reply_markup=cancel_keyboard())


@router.callback_query(F.data.startswith("admin:delch:"))
async def delete_channel(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    try:
        chat_id = int((callback.data or "").split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("⚠️ Noto'g'ri kanal", show_alert=True)
        return

    await db.delete_channel(chat_id)
    await callback.answer("✅ Kanal o'chirildi")
    message = callback_message(callback)
    if message:
        await _render_channels(message, db, edit=True)


@router.message(AdminFlow.channel)
async def receive_channel(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    chat = None

    if isinstance(message.forward_origin, MessageOriginChannel):
        chat = message.forward_origin.chat
    elif message.text:
        raw: str | int = message.text.strip()
        if raw.startswith(("https://", "http://")):
            raw = raw.rstrip("/").split("/")[-1]
            if not raw:
                await message.answer(CHANNEL_NOT_FOUND)
                return
        if isinstance(raw, str) and raw.lstrip("-").isdigit():
            raw = int(raw)
        elif isinstance(raw, str) and not raw.startswith("@"):
            raw = "@" + raw

        try:
            chat = await bot.get_chat(raw)
        except TelegramAPIError:
            await message.answer(CHANNEL_NOT_FOUND)
            return

    if chat is None or chat.type != ChatType.CHANNEL:
        await message.answer(CHANNEL_NOT_CHANNEL)
        return

    me = await bot.get_me()
    try:
        member = await bot.get_chat_member(chat.id, me.id)
    except TelegramAPIError:
        await message.answer(CHANNEL_CHECK_FAILED)
        return

    if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
        await message.answer(
            CHANNEL_BOT_NOT_ADMIN.format(title=escape(chat.title or "kanal"))
        )
        return

    link: str | None = None
    if chat.username:
        link = f"https://t.me/{chat.username}"
    else:
        try:
            link = await bot.export_chat_invite_link(chat.id)
        except TelegramAPIError:
            link = None

    if not link:
        await message.answer(CHANNEL_NO_LINK)
        return

    await db.add_channel(
        chat_id=chat.id,
        title=chat.title or "Kanal",
        username=chat.username,
        invite_link=link,
        added_by=message.from_user.id if message.from_user else None,
    )
    await state.clear()
    await message.answer(
        CHANNEL_ADDED.format(title=escape(chat.title or "Kanal")),
        reply_markup=admin_back_keyboard(),
    )


# ---------------------------------------------------------------- statistika


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery, db: Database) -> None:
    total = await db.count_users()
    today = await db.count_new_users_today()
    translations = await db.count_translations()
    channels = await db.get_channels()

    text = ADMIN_STATS.format(
        total=total,
        today=today,
        translations=translations,
        channels=len(channels),
    )
    await callback.answer()
    message = callback_message(callback)
    if message:
        await _safe_edit(message, text, admin_back_keyboard())
