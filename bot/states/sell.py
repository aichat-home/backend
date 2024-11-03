from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import swap_confirmation, to_home
from bot.image import start_photo
from utils import wallet
from models import Settings
from utils.swap import swap



class SellState(StatesGroup):
    percent = State()
    amount = State()
    confirmation = State()


async def sell_token(message: Message, state: FSMContext, session: AsyncSession):

    db_wallet = await wallet.get_wallet_by_id(session, message.from_user.id)

    current_state = await state.get_state()
    data = await state.get_data()

    token_data = data.get('token_data', {})

    token = await wallet.get_token(db_wallet.public_key, token_data['address'])
    mint, balance, decimals = wallet.parse_token_mint_address_amount_decimals(token.value[0])


    if current_state == SellState.amount.state:
        text = message.text
        try:
            amount = float(text)
            if amount > balance:
                await message.answer_photo(photo=start_photo, caption='Amount exceeds your balance.', reply_markup=to_home())
                return
            await state.update_data(amount=amount)
            await state.set_state(SellState.confirmation.state)
        except ValueError:
            await message.answer_photo(photo=start_photo, caption='Invalid amount. Please enter a number.', reply_markup=to_home())
            return
    elif current_state == SellState.percent.state:
        text = message.text
        try:
            percent = float(text)
            if percent <= 0 or percent > 100:
                await message.answer_photo(photo=start_photo, caption='Percent must be between 0 and 100.', reply_markup=to_home())
                return
            amount = balance * (percent / 100)
            
            await state.update_data(amount=amount)
            await state.set_state(SellState.confirmation.state)
        except ValueError:
            await message.answer_photo(photo=start_photo, caption='Invalid percent. Please enter a number.', reply_markup=to_home())
            return
    settings = await session.get(Settings, message.from_user.id)

    if settings.extra_confirmation:
        await message.answer_photo(
            photo=start_photo, 
            caption=f'You are about to sell {amount} {token_data["symbol"].upper()} for SOL. Please confirm.',
            reply_markup=swap_confirmation()
        )
        return
    
    await swap.sell_token(
        token_data=token_data,
        db_wallet=db_wallet,
        slippage=settings.sell_slippage,
        amount=amount,
        message_or_callback=message,
        session=session,
        photo=start_photo,
        decimals=decimals
    )

