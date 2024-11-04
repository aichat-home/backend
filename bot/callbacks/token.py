from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import buy_keyboard
from bot.texts import texts
from utils import market




router = Router()


@router.callback_query(F.data.startswith('token_'))
async def get_token(callback_query: CallbackQuery, session: AsyncSession):
    token_address = callback_query.data.split('_')[1]
    try:
        token_data = await market.get_token_data_by_address(session, token_address)
        if token_data:
            await callback_query.message.edit_caption(caption=texts.TOKEN_TEXT.format(
                name=token_data['name'],
                symbol=token_data['symbol'],
                price=token_data['price'],
                address=token_data['address'],
                decimals=token_data['decimals'],
                market_cap=token_data['market_cap'],
                total_volume=token_data['total_volume'],
                price_change_percentage_24h=token_data['price_change_percentage_24h']
            ),
            reply_markup=buy_keyboard(token_address)
            )
    except Exception:
        pass
    await callback_query.answer()
