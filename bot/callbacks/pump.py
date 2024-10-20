from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData

from sqlalchemy.ext.asyncio import AsyncSession

from utils import pump, wallet, market
from bot.keyboards import pump_keyboard, buy_keyboard
from bot.image import start_photo
from bot.callbacks.factory import TokenCallback


router = Router()


@router.callback_query(F.data == 'pump.fun')
async def get_new_tokens(callback_query: CallbackQuery):
    new_tokens = pump.get_last_20_tokens()

    await callback_query.message.edit_caption(caption='New tokens: ', reply_markup=pump_keyboard(new_tokens))
    await callback_query.answer()


@router.callback_query(TokenCallback.filter(F.symbol is not None))
async def buy_pump_tokens(callback_query: CallbackQuery, token_callback: TokenCallback, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)

    price = token_callback.v_sol_in_bonding_curve / token_callback.v_tokens_in_bondnig_curve

    text = (
            f'Buy <a href="https://solscan.io/token/{token_callback.mint}">🅴</a> <b>{token_callback.symbol.upper()}</b>\n'
            f'💳 My Balance: <code>{balance} SOL</code>\n\n'

            f'💸  Price: {price}\n'
            f'💵  MCap: ${market.format_number(token_callback.market_cap_sol)}\n'
            f'💰  Liqudity: ${market.format_number(token_callback.v_sol_in_bonding_curve)}\n'
        )
    
    await callback_query.message.edit_caption(caption=text, reply_markup=buy_keyboard(token_callback.mint))