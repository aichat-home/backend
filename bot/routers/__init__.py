from aiogram import Router

from .base_commands import router as base_router
from .waiting_for_message import router as waiting_for_message_router

router = Router()
router.include_router(base_router)
router.include_router(waiting_for_message_router)