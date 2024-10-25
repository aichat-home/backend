from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from utils import user as user_crud
from bot.keyboards import swap_confirmation, to_home
from bot.image import start_photo
from utils.swap import swap



class BuyState(StatesGroup):
    amount = State()
    confirmation = State()


async def buy_token(message: Message, state: FSMContext, session: AsyncSession):

    current_state = await state.get_state()
    data = await state.get_data()

    token_data = data.get('token_data', {})
    db_wallet = data.get('db_wallet')
    

    if current_state == BuyState.amount.state:
        text = message.text
        try:
            amount = float(text)
            await state.update_data(amount=amount)

            settings = await user_crud.get_settings(message.from_user.id, session)
            if settings.extra_confirmation:
                await state.set_state(BuyState.confirmation)
                
                text = f'You are about to buy {token_data["symbol"].upper()} for {amount} SOL . Please confirm.'
                await message.answer_photo(photo=start_photo, caption=text, reply_markup=swap_confirmation())
                return
            
            await swap.buy_token(
                token_data=token_data,
                db_wallet=db_wallet,
                slippage=settings.buy_slippage,
                amount=amount,
                message_or_callback=message,
                photo=start_photo,
                session=session
            )
            
        except Exception as e:
            print(e)
            await message.answer_photo(photo=start_photo, caption='Invalid amount. Please enter a number.', reply_markup=to_home())
            return
    
    
