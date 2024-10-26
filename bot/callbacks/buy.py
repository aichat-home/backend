from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from solders.keypair import Keypair # type: ignore

from utils import wallet, market, user as user_crud
from models import User, Settings
from session import get_session
from bot.keyboards import swap_confirmation, cancel_keyboard, to_home
from bot.states import tokens
from bot.states import buy, sell
from utils.swap import swap, raydium, utils



router = Router()


@router.callback_query(F.data == 'buy')
async def get_token(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(tokens.TokenState.token)
    await callback_query.message.edit_caption(caption=
        'Buy Token:\n\nTo buy a token enter a token address, or a URL from Birdeye',
        reply_markup=cancel_keyboard
        )
    await callback_query.answer()


@router.callback_query(F.data.startswith('buy_'))
async def buy_token(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)
    await state.update_data(db_wallet=db_wallet)

    data = callback_query.data.split('_')
    amount = data[1]
    token_address = data[2]
    
    client_session = get_session()
    token_data = await market.get_token_data_by_address(client_session, token_address)
    await state.update_data(token_data=token_data)

    if amount == 'x':
        await state.set_state(buy.BuyState.amount)
        await callback_query.message.edit_caption(caption=
            'Enter amount',
            reply_markup=to_home()
        )
        await callback_query.answer()
        return
    else:
        if float(amount) >= balance:
            amount = float(amount)
            await state.update_data(amount=amount)
            await state.set_state(buy.BuyState.confirmation)

            settings = await user_crud.get_settings(callback_query.from_user.id, session)

            if settings.extra_confirmation:
                await callback_query.message.edit_caption(caption=
                    f'You are about to buy {token_data["symbol"].upper()} for {amount} SOL . Please confirm.',
                    reply_markup=swap_confirmation()
                )
                await callback_query.answer()
                return
            await swap.buy_token(
                token_data=token_data,
                db_wallet=db_wallet,
                slippage=settings.buy_slippage,
                amount=amount,
                message_or_callback=callback_query,
                session=session
            )
        else:
            await callback_query.message.edit_caption(caption='Insufficient balance', reply_markup=to_home())
            return
        

@router.callback_query(F.data == 'confirm_swap')
async def confirm_swap(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state == buy.BuyState.confirmation or current_state == sell.SellState.confirmation:
        db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)

        data = await state.get_data()
        token_data = data.get('token_data')
        
        await swap.make_swap_with_callback(
                callback_query=callback_query,
                db_wallet=db_wallet,
                user_id=callback_query.from_user.id,
                data=data,
                token_data=token_data,
                session=session,
                state=state
            )
        