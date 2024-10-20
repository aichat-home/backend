from aiogram import Router
from .home import router as refresh_router
from .buy import router as buy_router
from .wallet import router as wallet_router
from .token import router as token_router
from .help import router as help_router
from .settings import router as settings_router
from .sell import router as sell_router
from .pump import router as pump_router


router = Router()
router.include_router(refresh_router)
router.include_router(buy_router)
router.include_router(wallet_router)
router.include_router(token_router)
router.include_router(help_router)
router.include_router(settings_router)
router.include_router(sell_router)
router.include_router(pump_router)