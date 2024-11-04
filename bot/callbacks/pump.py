from datetime import timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from utils import pump, wallet, market
from session import get_session
from bot.keyboards import pump_keyboard, buy_keyboard


router = Router()


@router.callback_query(F.data == 'pump.fun')
async def get_new_tokens(callback_query: CallbackQuery):
    await callback_query.answer('Coming soon!')
    # new_tokens = pump.get_last_20_tokens()
    # try:
    #     await callback_query.message.edit_caption(caption='New tokens: ', reply_markup=pump_keyboard(new_tokens))
    #     await callback_query.answer()
    # except Exception:
    #     await callback_query.answer()


@router.callback_query(F.data.startswith('pump_'))
async def buy_pump_tokens(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    await callback_query.answer()
    mint = callback_query.data.split('_')[1]
    client_session = get_session()
    token_data = await market.get_token_data_by_address(client_session, mint)

    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)
        
    text = (
            f'{token_data["name"]} <code>({token_data["symbol"]})</code>\n'
            f'<code>{mint}</code>\n'
            f'Creator: <code>{token_data["creator"]} - {token_data["time_passed"]}</code>\n\n'
            f'💳 My Balance: <code>{balance} SOL</code>\n\n'

            f'💸  Price: <code>${token_data["price"]}</code>\n'
            f'💵  MCap: <code>${market.format_number(token_data["usd_market_cap"])}</code>\n'
        )
    await state.update_data(token_data=token_data, db_wallet=db_wallet)
    try:
        await callback_query.message.edit_caption(caption=text, reply_markup=buy_keyboard(mint, refresh_prefix='pump'))
    except Exception:
        await callback_query.answer()