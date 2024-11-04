from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.texts import texts
from bot.keyboards import to_home
from core import settings



router = Router()


@router.callback_query(F.data == 'help')
async def refresh(callback_query: CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.HELP_TEXT.format(fee=settings.program_fee_percentage), reply_markup=to_home())

    await callback_query.answer()
