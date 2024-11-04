from aiogram.types import Message, FSInputFile, TelegramObject
from aiogram.filters import CommandStart, Command
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from bot.states import partner



router = Router()



ADMIN_IDS = (540314239, 1795945549)


@router.message(Command('create_partner'))
async def create_partner(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await state.set_state(partner.CreatePartnerState.waiting_for_name)
        await message.answer('Send name of partner')