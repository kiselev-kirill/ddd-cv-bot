from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag

from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender


class ChatActionMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):
        chat_action_type = get_flag(data, "chat_action")
        if not chat_action_type:
            return await handler(event, data)

        async with ChatActionSender(
                action=chat_action_type,
                chat_id=event.chat.id,
                bot=data["bot"],
        ):
            return await handler(event, data)