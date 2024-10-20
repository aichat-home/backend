from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from utils import wallet, swap
from models import User
from bot.keyboards import swap_confirmation, to_home
from bot.image import start_photo



class BuyState(StatesGroup):
    amount = State()
    confirmation = State()


async def buy_token(message: Message, state: FSMContext, session: AsyncSession):

    current_state = await state.get_state()
    data = await state.get_data()

    token_data = data.get('token_data', {})
    db_wallet = data.get('db_wallet')

    token = await wallet.get_token(db_wallet.public_key, token_data['address'])
    mint, balance, decimals = wallet.parse_token_mint_address_amount_decimals(token.value[0])

    await state.update_data(
    input_mint='So11111111111111111111111111111111111111112', 
    output_mint=token_data.get('address'),
    input_decimals=9,
    output_decimals=decimals
    )

    if current_state == BuyState.amount.state:
        text = message.text
        try:
            amount = float(text)
            await state.update_data(amount=amount)
            
            db_user = await session.get(User, message.from_user.id)
            if db_user.extra_confirmation:
                await state.set_state(BuyState.confirmation)
                
                text = f'You are about to buy {token_data["symbol"].upper()} for {amount} SOL . Please confirm.'
                await message.answer_photo(photo=start_photo, caption=text, reply_markup=swap_confirmation())
                return
            await swap.make_swap_with_message(
                message=message,
                db_wallet=db_wallet,
                user_id=message.from_user.id,
                token_data=token_data,
                data=await state.get_data(),
                session=session
            )
            
        except ValueError:
            await message.answer('Invalid amount. Please enter a number.', reply_markup=to_home())
            return
    
    
