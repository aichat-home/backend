from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import sniper_show_keyboar
from utils import sniper, wallet


router = Router()


@router.callback_query(F.data == 'sniper_bot')
async def get_new_tokens(callback_query: CallbackQuery, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.id)
    orders = await sniper.get_all_orders(db_wallet.id, session)
    await callback_query.message.edit_caption((f'Active Snipers: {len(orders)}\n\n'

                                'Paste token address to create new sniper!'
                                ),
                                reply_markup=sniper_show_keyboar()
                                )