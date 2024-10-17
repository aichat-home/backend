from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from core import settings
from bot.keyboards import withdraw_confirmation, cancel_withdraw
from bot.image import start_photo



class WithdrawState(StatesGroup):
    amount = State()
    receiver_address = State()
    confirm = State()


async def withdraw_state(state: FSMContext, message: Message):
    current_state = await state.get_state()
    if current_state == WithdrawState.amount:
        try:
            amount = float(message.text)
            await state.update_data(amount=amount)
            await state.set_state(WithdrawState.receiver_address)
            text = 'Enter receiver address'
        except ValueError:
            text = 'Invalid amount'
            return
        await message.answer_photo(photo=start_photo, caption=text, reply_markup=cancel_withdraw())
    elif current_state == WithdrawState.receiver_address:
        await state.update_data(receiver_address=message.text)
        await state.set_state(WithdrawState.confirm)

        data = await state.get_data()
        amount = data.get('amount')

        await state.update_data(receiver_address=message.text)
        text = ("You're about to send a transaction. Please check the details:\n\n"
                
                f"To: <b>{message.text}</b>\n"
                f"Amount: <b>{amount}</b> SOL\n"
                f"Fee: <b>{(amount * settings.program_fee_percentage) / 100}</b> SOL"
                )
        
        await message.answer_photo(photo=start_photo, caption=text, reply_markup=withdraw_confirmation())