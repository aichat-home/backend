import asyncio

from bot import dp, bot, router
from session import init_session
from utils import pump


async def main():
    init_session()

    asyncio.create_task(pump.websocket_handler())

    await bot.delete_webhook()

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())