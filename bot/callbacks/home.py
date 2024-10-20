from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts import texts
from bot.keyboards import start_keyboard
from utils import wallet



router = Router()


@router.callback_query(F.data == 'home')
async def refresh(callback_query: CallbackQuery, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)
    try:
        await callback_query.message.edit_caption(
            caption=texts.START_TEXT.format(
                balance=balance,
                wallet_address=db_wallet.public_key
            ),
            reply_markup=start_keyboard
        )
    except Exception as e:
        print(e)

    await callback_query.answer()
