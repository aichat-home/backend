from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from solders.transaction_status import TransactionConfirmationStatus # type: ignore
from solana.rpc.commitment import Finalized

from utils import wallet, market, swap
from models import User, Swap
from rpc import client
from session import get_session
from bot.keyboards import swap_confirmation, cancel_keyboard, to_home
from bot.states import tokens
from bot.states import buy, sell
from bot.texts import texts



router = Router()


@router.callback_query(F.data == 'buy')
async def get_token(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(tokens.TokenState.token)
    await callback_query.message.edit_caption(caption=
        'Buy Token:\n\nTo buy a token enter a token address, or a URL from Birdeye,',
        reply_markup=cancel_keyboard
        )
    await callback_query.answer()


@router.callback_query(F.data.startswith('buy_'))
async def buy_token(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    balance = await wallet.get_wallet_balance(db_wallet.public_key)
    await state.update_data(db_wallet=db_wallet)

    data = callback_query.data.split('_')
    amount = data[1]
    token_address = data[2]
    
    client_session = get_session()
    token_data = await market.get_token_data_by_address(client_session, token_address)
    await state.update_data(token_data=token_data)

    if amount == 'x':
        await state.set_state(buy.BuyState.amount)
        await callback_query.message.edit_caption(caption=
            'Enter amount',
            reply_markup=to_home()
        )
        await callback_query.answer()
        return
    else:
        if float(amount) <= balance:
            amount = balance
            await state.update_data(amount=amount)
            await state.set_state(buy.BuyState.confirmation)

            await callback_query.message.edit_caption(caption=
                f'You are about to buy {token_data["symbol"].upper()} for {amount} SOL . Please confirm.',
                reply_markup=swap_confirmation()
            )
            await callback_query.answer()
            return
        else:
            await callback_query.message.edit_caption(caption='Insufficient balance', reply_markup=to_home())
            return
        

@router.callback_query(F.data == 'confirm_swap')
async def confirm_swap(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state == buy.BuyState.confirmation or current_state == sell.SellState.confirmation:
        db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
        db_user = await session.get(User, callback_query.from_user.id)

        data = await state.get_data()
        token_data = data.get('token_data')

        if token_data['address'] == data.get('input_mint'):
            slippage = db_user.sell_slippage * 100
        else:
            slippage = db_user.buy_slippage * 100

        response = await swap.swap(
            db_wallet.encrypted_private_key, 
            data.get('input_mint'), 
            data.get('output_mint'),
            data.get('amount'),
            int(slippage),
            data.get('decimals')
            )
        await callback_query.message.edit_caption(caption='Transaction sent. Waiting for confirmation...')
        try:
            tx_sig, quote_response = response
            swap_record = Swap(
                wallet=db_wallet.id,
                input_mint=quote_response['inputMint'],
                output_mint=quote_response['outputMint'],
                input_amount=int(quote_response['inAmount']),
                output_amount=int(quote_response['outAmount']),
                status='Waiting for Confirmation',
                date=datetime.now()
                )
            session.add(swap_record)
            await session.commit()


            confirmation = await client.confirm_transaction(tx_sig, commitment=Finalized, sleep_seconds=5)
            if confirmation.value:
                if confirmation.value[0].confirmation_status == TransactionConfirmationStatus.Finalized:
                    if token_data['address'] == quote_response['inputMint']:
                        input_symbol = token_data['symbol'].upper()
                        output_symbol = 'SOL'
                        input_decimals = data.get('decimals')
                        output_decimals = 9
                    else:
                        input_symbol = 'SOL'
                        output_symbol = token_data['symbol'].upper()
                        input_decimals = 9
                        output_decimals = data.get('decimals')
                    text = texts.SUCCESSFULL_TRANSACTION.format(
                            input_symbol=input_symbol, output_symbol=output_symbol,
                            in_amount=float(quote_response['inAmount']) / 10 ** input_decimals,
                            out_amount=float(quote_response['outAmount']) / 10 ** output_decimals,
                        )
                    await callback_query.message.edit_caption(caption=text, reply_markup=to_home())
                    swap_record.status = 'Finalized'
                    await session.commit()
                    
            await state.clear()
        except Exception as e:
            await callback_query.message.edit_caption(caption='Transaction failed!', reply_markup=to_home())
            swap_record.status = 'Failed'
            await session.commit()
            print(e)
            await state.clear()
            return