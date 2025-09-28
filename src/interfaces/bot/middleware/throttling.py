from datetime import datetime
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.dispatcher.flags import get_flag
from cachetools import TTLCache


user_last_time = TTLCache(maxsize=1000, ttl=10)


class ThrottlingMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message, data: dict[str, Any]):
        rate_limit = get_flag(data, "rate_limit")
        if rate_limit is None:
            return await handler(event, data)

        user_id = event.from_user.id
        now = datetime.now().timestamp()
        last = user_last_time.get(user_id)
        if not last:
            user_last_time[user_id] = now
            return await handler(event, data)
        if now - last < rate_limit:
            await event.answer("Слишком быстро, тигр🐯\n"
                               "Подождите немного\\.\\.\\.⏳")
            return
