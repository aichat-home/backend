import asyncio

from bot import dp, bot, router
from session import init_session


async def main():
    init_session()
    await bot.delete_webhook()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())