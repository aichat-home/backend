from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.keyboards import swap_confirmation, to_home
from bot.image import start_photo



class BuyState(StatesGroup):
    amount = State()
    confirmation = State()


async def buy_token(message: Message, state: FSMContext):

    current_state = await state.get_state()
    data = await state.get_data()

    token_data = data.get('token_data', {})

    await state.update_data(
    input_mint='So11111111111111111111111111111111111111112', 
    output_mint=token_data.get('address'),
    decimals=9
    )

    if current_state == BuyState.amount.state:
        text = message.text
        try:
            amount = float(text)
            await state.update_data(amount=amount)
            await state.set_state(BuyState.confirmation)

            text = f'You are about to buy {token_data["symbol"].upper()} for {amount} SOL . Please confirm.'
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=swap_confirmation())

        except ValueError:
            await message.answer('Invalid amount. Please enter a number.', reply_markup=to_home())
            return
    
    
