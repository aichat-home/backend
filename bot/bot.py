from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from core import settings
from db import database
from bot.middlewares import DbSessionMiddleware, OnlyDMMiddleware


bot = Bot(settings.telegram_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.update.middleware(DbSessionMiddleware(database))
dp.update.middleware(OnlyDMMiddleware())