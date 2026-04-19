import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand, BotCommandScopeDefault

from src.config import settings
from src.interfaces.bot.constants import get_bot_commands
from src.interfaces.bot.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES

from src.interfaces.bot.handlers.chat import router as chat_router
from src.interfaces.bot.middleware.action import ChatActionMiddleware
from src.interfaces.bot.middleware.throttling import ThrottlingMiddleware


async def _register_bot_commands(bot: Bot) -> None:
    default_commands = [
        BotCommand(command=command, description=description)
        for command, description in get_bot_commands(DEFAULT_LOCALE)
    ]
    await bot.set_my_commands(
        commands=default_commands,
        scope=BotCommandScopeDefault(),
    )

    for locale in sorted(SUPPORTED_LOCALES):
        commands = [
            BotCommand(command=command, description=description)
            for command, description in get_bot_commands(locale)
        ]
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeDefault(),
            language_code=locale,
        )


async def main():
    session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="MarkdownV2"))
    try:
        dp = Dispatcher()
        dp.include_router(chat_router)
        await _register_bot_commands(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        dp.message.middleware(ChatActionMiddleware())
        dp.message.middleware(ThrottlingMiddleware())
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
