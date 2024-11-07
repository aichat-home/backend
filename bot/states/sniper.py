from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from utils import wallet, metaplex
from models import Order
from session import get_session
from bot.keyboards import sniper_token, edit_sniper_token
from bot.image import start_photo



class SnipeState(StatesGroup):
    token = State()
    amount = State()
    slippage = State()
    gas = State()


class EditSniperState(StatesGroup):
    token = State()
    amount = State()
    slippage = State()
    gas = State()


async def snipe_token(message: Message, state: FSMContext, session: AsyncSession):

    current_state = await state.get_state()
    data = await state.get_data()


    if current_state == SnipeState.token.state:
        token_data = await metaplex.get_metadata(message.text)
        if token_data:
            token_data['address'] = message.text
            db_wallet = await wallet.get_wallet_by_id(session, message.from_user.id)
            balance = await wallet.get_wallet_balance(db_wallet.public_key)
            await state.update_data(token_data=token_data, db_wallet=db_wallet, balance=balance)

            text = (
                    f'Snipe <a href="https://solscan.io/token/{message.text}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                    f'💳 My Balance: <code>{balance} SOL</code>'
                )
            slippage = data.get('slippage', 15)
            gas = data.get('gas', 0.001)
            amount = data.get('amount', 0.1)
            mev = data.get('mev', True)
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=sniper_token(slippage, gas, amount, message.text, mev))
        
    elif current_state == SnipeState.slippage.state:
        try:
            data = await state.get_data()
            slippage = float(message.text)
            if 1 <= slippage <= 100:
                await state.update_data(slippage=slippage)
                token_data = data.get('token_data', {})
                balance = data.get('balance', 0)

                text = (
                    f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                    f'💳 My Balance: <code>{balance} SOL</code>'
                )
                gas = data.get('gas', 0.001)
                amount = data.get('amount', 0.1)
                mev = data.get('mev', True)
                
                await message.answer_photo(photo=start_photo, caption=text, reply_markup=sniper_token(slippage, gas, amount, token_data['address'], mev))
            else:
                await message.answer(text='Invalid slippage value. Please enter a number between 1 and 100')
        except Exception as e:
            print(e)
            await message.answer(text='Invalid slippage value. Please enter a number between 1 and 100')
    elif current_state == SnipeState.amount.state:
        try:
            data = await state.get_data()
            amount = float(message.text)
            await state.update_data(amount=amount)
            token_data = data.get('token_data', {})
            balance = data.get('balance', 0)

            text = (
                f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                f'💳 My Balance: <code>{balance} SOL</code>'
            )
            gas = data.get('gas', 0.001)
            slippage = data.get('slippage', 15)
            mev = data.get('mev', True)
            
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=sniper_token(slippage, gas, amount, token_data['address'], mev))
        except Exception as e:
            print(e)
            await message.answer(text='Invalid amount')            
    elif current_state == SnipeState.gas.state:
        try:
            data = await state.get_data()
            gas = float(message.text)
            await state.update_data(gas=gas)
            token_data = data.get('token_data', {})
            balance = data.get('balance', 0)

            text = (
                f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                f'💳 My Balance: <code>{balance} SOL</code>'
            )
            amount = data.get('amount', 0.1)
            slippage = data.get('slippage', 15)
            mev = data.get('mev', True)
            
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=sniper_token(slippage, gas, amount, token_data['address'], mev))
        except Exception as e:
            print(e)
            await message.answer(text='Invalid amount')  

    elif current_state == EditSniperState.amount.state:
        try:
            amount = float(message.text)
            data = await state.get_data()
            order: Order = data.get('order')
            order.sol_amount = amount
            session.add(order)
            await session.commit()
            print(data)

            db_wallet = data.get('db_wallet')
            
            token_data = data.get('token_data', {})
            balance = data.get('balance', 0)

            text = (
                f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                f'💳 My Balance: <code>{balance} SOL</code>'
            )
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=edit_sniper_token(order.slippage, order.gas, order.sol_amount, order.mev_protection, order.id))

        except Exception as e:
            print(e)
            await message.answer(text='Invalid amount')  
    elif current_state == EditSniperState.slippage.state:
        try:
            data = await state.get_data()
            order: Order = data.get('order')
            slippage = float(message.text)
            if 1 <= slippage <= 100:
                order.slippage = slippage
                session.add(order)
                await session.commit()

                db_wallet = data.get('db_wallet')
                

                token_data = data.get('token_data', {})
                balance = data.get('balance', 0)

                text = (
                    f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                    f'💳 My Balance: <code>{balance} SOL</code>'
                )
                await message.answer_photo(photo=start_photo, caption=text, reply_markup=edit_sniper_token(order.slippage, order.gas, order.sol_amount, order.mev_protection, order.id))
            else:
                await message.answer(text='Invalid slippage value. Please enter a number between 1 and 100')
        except Exception as e:
            print(e)
            await message.answer(text='Invalid slippage value. Please enter a number between 1 and 100')
    elif current_state == EditSniperState.gas.state:
        try:
            data = await state.get_data()
            order: Order = data.get('order')
            gas = float(message.text)
            order.gas = gas
            session.add(order)
            await session.commit()

            db_wallet = data.get('db_wallet')
            

            token_data = data.get('token_data', {})
            balance = data.get('balance', 0)

            text = (
                f'Snipe <a href="https://solscan.io/token/{token_data["address"]}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                f'💳 My Balance: <code>{balance} SOL</code>'
            )
            await message.answer_photo(photo=start_photo, caption=text, reply_markup=edit_sniper_token(order.slippage, order.gas, order.sol_amount, order.mev_protection, order.id))
        except Exception as e:
            print(e)
            await message.answer(text='Invalid value')

                

            