from aiogram import Router, F
from aiogram.types import CallbackQuery



router = Router()


@router.callback_query(F.data == 'sniper_bot')
async def get_new_tokens(callback_query: CallbackQuery):
    await callback_query.answer('Coming soon!')