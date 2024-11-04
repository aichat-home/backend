from typing import Callable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject



class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db  # Your database service that has `get_async_session`

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Any],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        # Generate a session using the async session generator
        async for session in self.db.get_async_session():
            # Inject session into data (so handlers can access it)
            data['session'] = session

            # Proceed with the handler
            return await handler(event, data)