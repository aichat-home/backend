from aiogram import Router

from .base_commands import router as base_router
from .waiting_for_message import router as waiting_for_message_router
from .create_partners import router as partner_router

router = Router()
router.include_router(base_router)
router.include_router(partner_router)
router.include_router(waiting_for_message_router)