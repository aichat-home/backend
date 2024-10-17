from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import tokens, withdraw, settings, buy, sell


router = Router()


@router.message()
async def waiting_for_message(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state:
        if current_state in (withdraw.WithdrawState.amount, withdraw.WithdrawState.receiver_address):
            await withdraw.withdraw_state(state, message)
            return
        elif current_state in (settings.SlippageState.buy_slippage, settings.SlippageState.sell_slippage):
            await settings.change_slippage(message, state, session)
            return
        elif current_state in (buy.BuyState.amount, buy.BuyState.confirmation):
            await buy.buy_token(message, state)
            return
        elif current_state in (sell.SellState.amount, sell.SellState.percent, sell.SellState.confirmation):
            await sell.sell_token(message, state, session)
            return
    
    await state.set_state(tokens.TokenState.token)
    await tokens.handle_token(message, state, session)