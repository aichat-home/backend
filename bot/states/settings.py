from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import to_home
from bot.image import start_photo
from models import User



class SlippageState(StatesGroup):
    buy_slippage = State()
    sell_slippage = State()
    


async def change_slippage(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user: User = data.get('user')
    current_state = await state.get_state()

    try:
        amount = float(message.text)
        if amount < 1 or amount > 100:
            await message.answer_photo(photo=start_photo, caption='Slippage value must be between 1 and 100')
            return
    except ValueError:
        await message.answer_photo(photo=start_photo, caption='Invalid slippage value. Please enter a number between 1 and 100')
        return

    if current_state == SlippageState.buy_slippage:
        option = 'buy'
        user.buy_slippage = amount
        session.add(user)
        await session.commit()
    elif current_state == SlippageState.sell_slippage:
        option ='sell'
        user.sell_slippage = amount
        session.add(user)
        await session.commit()

    await message.answer_photo(photo=start_photo, caption=f'Slippage value for {option} set to {amount}%', reply_markup=to_home())
    await state.clear()

        