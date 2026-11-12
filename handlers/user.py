"""Foydalanuvchi bilan ishlash: matn qabul qilish va tarjima."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
)

import config
import translator
from database import Database
from keyboards import languages_keyboard, subscription_keyboard
from middlewares.subscription import SUB_CHECK_CALLBACK, get_missing_channels
from texts import (
    ADMIN_ONLY,
    DETECTED,
    FOREIGN_BUTTON,
    HELP,
    LONG_NOTE,
    NON_TEXT,
    RESULT_FOOTER,
    RESULT_HEADER,
    SHORT_TEXT,
    STALE_TEXT,
    SUBSCRIBED_OK,
    SUBSCRIBED_STILL,
    TRANSLATE_ERROR,
    UNKNOWN_COMMAND,
    WELCOME,
)
from utils import callback_message, escape, html_split, shorten

logger = logging.getLogger(__name__)

router = Router(name="user")
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if user is None:
        return
    await db.add_user(user.id, user.username, user.full_name)

    text = WELCOME.format(name=escape(user.first_name or "do'stim"))
    if user.id in config.ADMIN_IDS:
        text += "\n\n🛠 <b>Admin panel:</b> /admin"
    await message.answer(text, link_preview_options=NO_PREVIEW)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP, link_preview_options=NO_PREVIEW)


@router.message(Command("admin"))
async def admin_denied(message: Message) -> None:
    await message.answer(ADMIN_ONLY)


@router.callback_query(F.data == SUB_CHECK_CALLBACK)
async def check_subscription(callback: CallbackQuery, db: Database, bot: Bot) -> None:
    channels = await db.get_channels()
    if not channels:
        await callback.answer("✅ Majburiy kanallar yo'q")
        return

    missing = await get_missing_channels(bot, callback.from_user.id, channels)
    if missing:
        await callback.answer(SUBSCRIBED_STILL, show_alert=True)
        message = callback_message(callback)
        if message:
            try:
                await message.edit_reply_markup(reply_markup=subscription_keyboard(missing))
            except TelegramAPIError:
                pass
        return

    await callback.answer("✅ Obuna tasdiqlandi!")
    message = callback_message(callback)
    if message:
        try:
            await message.edit_text(
                SUBSCRIBED_OK,
                reply_markup=None,
                link_preview_options=NO_PREVIEW,
            )
        except TelegramAPIError:
            pass


@router.callback_query(F.data.startswith("tr:"))
async def choose_language(callback: CallbackQuery, db: Database) -> None:
    pieces = (callback.data or "").split(":")
    if len(pieces) != 3:
        await callback.answer()
        return

    _, raw_id, target = pieces
    message = callback_message(callback)

    if raw_id == "close":
        if message:
            try:
                await message.delete()
            except TelegramAPIError:
                try:
                    await message.edit_reply_markup(reply_markup=None)
                except TelegramAPIError:
                    pass
        await callback.answer()
        return

    if message is None:
        await callback.answer(STALE_TEXT, show_alert=True)
        return

    try:
        text_id = int(raw_id)
    except ValueError:
        await callback.answer(STALE_TEXT, show_alert=True)
        return

    row = await db.get_text(text_id)
    if row is None:
        await callback.answer(STALE_TEXT, show_alert=True)
        return
    if row["user_id"] != callback.from_user.id:
        await callback.answer(FOREIGN_BUTTON, show_alert=True)
        return

    try:
        translated, source = await translator.translate(row["text"], target)
    except translator.TranslationError:
        logger.exception("Tarjima qilishda xatolik (text_id=%s, target=%s)", text_id, target)
        await callback.answer(TRANSLATE_ERROR, show_alert=True)
        return

    info = translator.LANGUAGES.get(translator.normalize(target))
    if info is None:
        await callback.answer(TRANSLATE_ERROR, show_alert=True)
        return

    header = RESULT_HEADER.format(flag=info["flag"], native=info["native"])
    footer = RESULT_FOOTER.format(source=translator.label(source))
    await callback.answer()
    await _show_translation(
        message,
        header,
        translated,
        footer,
        languages_keyboard(text_id),
    )


async def _show_translation(
    message: Message,
    header: str,
    body: str,
    footer: str,
    keyboard: InlineKeyboardMarkup,
) -> None:
    """Tarjimani chiroyli ko'rinishda ko'rsatadi (uzun matnni bo'lib)."""
    chunks = html_split(body, 3000)
    note = LONG_NOTE.format(count=len(chunks)) if len(chunks) > 1 else ""
    first = f"{header}\n\n<blockquote>{chunks[0]}</blockquote>{note}{footer}"

    try:
        await message.edit_text(first, reply_markup=keyboard, link_preview_options=NO_PREVIEW)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        try:
            await message.answer(first, reply_markup=keyboard, link_preview_options=NO_PREVIEW)
        except TelegramAPIError:
            logger.exception("Tarjimani yuborib bo'lmadi")
            return
    except TelegramAPIError:
        logger.exception("Tarjimani tahrirlab bo'lmadi")
        return

    for chunk in chunks[1:]:
        try:
            await message.answer(
                f"<blockquote>{chunk}</blockquote>",
                link_preview_options=NO_PREVIEW,
            )
        except TelegramAPIError:
            logger.exception("Tarjima qismini yuborib bo'lmadi")
            break


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback_denied(callback: CallbackQuery) -> None:
    await callback.answer(ADMIN_ONLY, show_alert=True)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, db: Database) -> None:
    text = (message.text or "").strip()
    if not text:
        return
    if len(text) < 2:
        await message.answer(SHORT_TEXT)
        return

    user = message.from_user
    if user is None:
        return

    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except TelegramAPIError:
        pass

    source = await translator.detect(text)
    text_id = await db.save_text(user.id, text, source)

    preview = escape(shorten(text, 250))
    await message.answer(
        DETECTED.format(lang=translator.label(source), preview=preview),
        reply_markup=languages_keyboard(text_id),
        link_preview_options=NO_PREVIEW,
    )


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message) -> None:
    await message.answer(UNKNOWN_COMMAND)


@router.message()
async def other_content(message: Message) -> None:
    await message.answer(NON_TEXT)
