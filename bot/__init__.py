from aiogram.types import FSInputFile
from aiogram import Router

from .routers import router as main_router
from .callbacks import router as callbacks_router
from .bot import bot, dp




router = Router()
router.include_router(main_router)
router.include_router(callbacks_router)

media = FSInputFile('bot/media/video.mp4')