"""5 tilli tarjimon Telegram bot — kirish nuqtasi."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from aiogram.types.error_event import ErrorEvent

import config
import translator
from database import Database
from handlers import admin, user
from middlewares.subscription import SubscriptionMiddleware

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def set_commands(bot: Bot) -> None:
    user_commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish"),
        BotCommand(command="help", description="ℹ️ Yordam"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    admin_commands = [
        *user_commands,
        BotCommand(command="admin", description="🛠 Admin panel"),
    ]
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except TelegramAPIError:
            logger.warning("Admin %s uchun buyruqlar o'rnatilmadi", admin_id)


async def main() -> None:
    setup_logging()

    if not config.BOT_TOKEN:
        raise SystemExit(
            "\n❌ BOT_TOKEN topilmadi!\n"
            "1. .env.example faylidan nusxa oling va nomini .env qiling.\n"
            "2. @BotFather dan olingan tokenni BOT_TOKEN= qatoriga yozing.\n"
        )

    if not config.ADMIN_IDS:
        logger.warning("ADMIN_IDS bo'sh — admin panel ishlamaydi. .env ga ID yozing.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    db = Database(config.DB_PATH)
    await db.connect()

    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db

    subscription = SubscriptionMiddleware(db)
    dp.message.middleware(subscription)
    dp.callback_query.middleware(subscription)

    dp.include_router(admin.router)
    dp.include_router(user.router)

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        logger.error("Xatolik yuz berdi: %r", event.exception, exc_info=event.exception)
        return True

    await set_commands(bot)

    logger.info("Bot ishga tushdi. Adminlar: %s", sorted(config.ADMIN_IDS) or "yo'q")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await translator.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot to'xtatildi.")
