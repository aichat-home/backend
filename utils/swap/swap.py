from datetime import datetime

from aiogram.types import CallbackQuery, Message

from sqlalchemy.ext.asyncio import AsyncSession

from solders.keypair import Keypair # type: ignore
from .. import wallet, user as user_crud
from . import raydium, utils, constants
from bot.keyboards import to_home
from bot.texts import texts
from models import SolanaWallet, Swap
from session import get_session




async def create_swap_in_db(
        wallet_id: int, 
        session: AsyncSession,
        input_mint: str,
        output_mint: str,
        input_amount: int,
        output_amount: int,
        txn_sig: str
        ) -> Swap:
    swap_record = Swap(
        wallet=wallet_id,
        input_mint=input_mint,
        output_mint=output_mint,
        input_amount=input_amount,
        output_amount=output_amount,
        txn_sig=txn_sig,
        status='Waiting for Confirmation',
        date=datetime.now()
        )
    session.add(swap_record)
    await session.commit()
    return swap_record




async def end_swap(swap: Swap, db_wallet: SolanaWallet, user_id, trading_points: float, session: AsyncSession):
    swap.status = 'Finalized'
    await session.commit()

    db_wallet.number_of_trades += 1
    db_wallet.trading_points_earned += trading_points
    await user_crud.update_wallet(session, user_id, trading_points)


async def buy_token(
        token_data: dict,
        db_wallet: SolanaWallet,
        slippage: float,
        amount: int,
        message_or_callback: Message | CallbackQuery,
        session: AsyncSession,
        photo = None,
    ):
    client_session = get_session()

    pair_address = await utils.get_pair_address(token_data.get('address'), client_session)
    payer_keypair = Keypair.from_seed(wallet.decrypt_private_key(db_wallet.encrypted_private_key))
    response = await raydium.buy(pair_address, amount, slippage, payer_keypair)
    if response:
        if response['status'] == 'Confirmed':
            if isinstance(message_or_callback, Message):
                await message_or_callback.answer_photo(photo=photo, caption='Transaction sent. Waiting for confirmation...')
            else:
                await message_or_callback.message.edit_caption(caption='Transaction sent. Waiting for confirmation...')
            swap_db = await create_swap_in_db(
                    db_wallet.id,
                    session,
                    constants.SOL,
                    token_data['address'],
                    response['amount_in'] * constants.SOL_DECIMAL,
                    response['minimum_amount_out'] * (10 ** response['token_decimal']),
                    str(response['txn_sig'])
                )
            confirmed = await utils.confirm_txn(response['txn_sig'])
            if confirmed:
                trading_points = response['minimum_amount_out'] * token_data['price']
                text = texts.SUCCESSFULL_TRANSACTION.format(
                    input_symbol='SOL',
                    output_symbol=token_data['symbol'],
                    in_amount=response['amount_in'],
                    out_amount=response['minimum_amount_out'],
                    fee_amount=response['fee_amount'],
                    txn_sig=str(response['txn_sig']),
                    trading_points=trading_points
                )
                if isinstance(message_or_callback, Message):
                    await message_or_callback.answer_photo(photo=photo, caption=text, reply_markup=to_home())
                else:
                    await message_or_callback.message.edit_caption(caption=text, reply_markup=to_home())

                await end_swap(
                    swap=swap_db, 
                    db_wallet=db_wallet, 
                    user_id=message_or_callback.from_user.id, 
                    trading_points=trading_points,
                    session=session
                    )

                return

    text = f'Transaction failed\nView on <a href="https://solscan.io/tx/{str(response["txn_sig"])}">Solscan</a>'
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer_photo(photo=photo, caption=text, reply_markup=to_home())
        return
    await message_or_callback.message.edit_caption(caption=text, reply_markup=to_home())



async def sell_token(
        token_data: dict,
        db_wallet: SolanaWallet,
        slippage: float,
        amount: int,
        message_or_callback: Message | CallbackQuery,
        session: AsyncSession,
        photo = None,
    ):
    client_session = get_session()

    pair_address = await utils.get_pair_address(token_data['address'], client_session)
    payer_keypair = Keypair.from_seed(wallet.decrypt_private_key(db_wallet.encrypted_private_key))
    response = await raydium.sell(pair_address, amount, slippage, payer_keypair)

    if response:
        if response['status'] == 'Confirmed':
            if isinstance(message_or_callback, Message):
                await message_or_callback.answer_photo(photo=photo, caption='Transaction sent. Waiting for confirmation...')
            else:
                await message_or_callback.message.edit_caption(caption='Transaction sent. Waiting for confirmation...')
            
            swap_db = await create_swap_in_db(
                db_wallet.id,
                session,
                token_data['address'],
                constants.SOL,
                response['token_in'] * (10 ** response['token_decimal']),
                response['sol_out'] * constants.SOL_DECIMAL,
                str(response['txn_sig'])
            )
            
            confirmed = await utils.confirm_txn(response['txn_sig'])
            if confirmed:
                trading_points = response['token_in'] * token_data['price']
                text = texts.SUCCESSFULL_TRANSACTION.format(
                    input_symbol=token_data['symbol'],
                    output_symbol='SOL',
                    in_amount=response['token_in'],
                    out_amount=response['sol_out'],
                    fee_amount=response['fee_amount'],
                    txn_sig=str(response['txn_sig']),
                    trading_points=trading_points
                )
                if isinstance(message_or_callback, Message):
                    await message_or_callback.answer_photo(photo=photo, caption=text, reply_markup=to_home())
                else:
                    await message_or_callback.message.edit_caption(caption=text, reply_markup=to_home())

                await end_swap(
                    swap=swap_db, 
                    db_wallet=db_wallet, 
                    user_id=message_or_callback.from_user.id, 
                    trading_points=trading_points,
                    session=session
                    )
                return
            
            