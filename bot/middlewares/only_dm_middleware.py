from typing import Callable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject



class OnlyDMMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Any],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        # Generate a session using the async session generator
        try:
            if event.message.chat.type == "private":    
                return await handler(event, data)
        except Exception as e:
            print(e)  
            return await handler(event, data)
            