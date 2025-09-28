import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from src.config import settings

from src.interfaces.bot.handlers.chat import router as chat_router
from src.interfaces.bot.middleware.action import ChatActionMiddleware
from src.interfaces.bot.middleware.throttling import ThrottlingMiddleware


async def main():
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="MarkdownV2"))
    dp = Dispatcher()
    dp.include_router(chat_router)
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.middleware(ChatActionMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())