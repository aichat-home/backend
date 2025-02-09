from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import tokens, withdraw, settings, buy, sell, sniper, partner


router = Router()


@router.message()
async def waiting_for_message(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state:
        if current_state in (withdraw.WithdrawState.amount, withdraw.WithdrawState.receiver_address):
            await withdraw.withdraw_state(state, message, session)
            return
        elif current_state in (settings.SlippageState.buy_slippage, settings.SlippageState.sell_slippage):
            await settings.change_slippage(message, state, session)
            return
        elif current_state in (buy.BuyState.amount, buy.BuyState.confirmation):
            await buy.buy_token(message, state, session)
            return
        elif current_state in (sniper.SnipeState.token, sniper.SnipeState.amount, sniper.SnipeState.slippage, sniper.SnipeState.gas, sniper.EditSniperState.token, sniper.EditSniperState.amount, sniper.EditSniperState.slippage, sniper.EditSniperState.gas):
            await sniper.snipe_token(message, state, session)
            return 
        elif current_state in (sell.SellState.amount, sell.SellState.percent, sell.SellState.confirmation):
            await sell.sell_token(message, state, session)
            return
        elif current_state == partner.CreatePartnerState.waiting_for_name:
            await partner.create_partner(message, session)
            return 
    
    await state.set_state(tokens.TokenState.token)
    await tokens.handle_token(message, state, session)