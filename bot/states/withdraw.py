from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from solders.transaction_status import TransactionConfirmationStatus # type: ignore
from solana.rpc.commitment import Finalized

from core import settings
from models import User
from utils import wallet
from rpc import client
from bot.keyboards import withdraw_confirmation, cancel_withdraw, to_home
from bot.image import start_photo



class WithdrawState(StatesGroup):
    amount = State()
    receiver_address = State()
    confirm = State()


async def withdraw_state(state: FSMContext, message: Message, session: AsyncSession):
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
        db_user = await session.get(User, message.from_user.id)
        if db_user.extra_confirmation:
            text = ("You're about to send a transaction. Please check the details:\n\n"
                    
                    f"To: <b>{message.text}</b>\n"
                    f"Amount: <b>{amount}</b> SOL\n"
                    f"Fee: <b>{(amount * settings.program_fee_percentage) / 100}</b> SOL"
                    )
            
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=withdraw_confirmation())
            return 
        try:
            db_wallet = await wallet.get_wallet_by_id(session, message.from_user.id)
            tx_sig = await wallet.send_transaction(amount * 1_000_000_000, db_wallet.encrypted_private_key, message.text)
            await message.answer(text='Transaction sent. Waiting for confirmation...')

            confirmation = await client.confirm_transaction(tx_sig, commitment=Finalized, sleep_seconds=5)
            if confirmation.value:
                if confirmation.value[0].confirmation_status == TransactionConfirmationStatus.Finalized:
                    await message.answer_photo(photo=start_photo, caption='Transaction went successfull', reply_markup=to_home())
                    await state.clear()
        except Exception as e:
            print(e)
            await message.answer_photo(photo=start_photo, caption='Transaction failed', reply_markup=to_home())
            return