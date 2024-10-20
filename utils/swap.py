import json
import base64
from datetime import datetime

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solders.message import  to_bytes_versioned # type: ignore
from solders.transaction import VersionedTransaction # type: ignore
from solders.transaction_status import TransactionConfirmationStatus # type: ignore

from solana.rpc.commitment import Finalized
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed

from spl.token.constants import WRAPPED_SOL_MINT

from . import wallet, user as user_crud
from bot.keyboards import to_home
from bot.texts import texts
from models import SolanaWallet, User, Swap
from rpc import metis_client as client
from session import get_session



async def get_quote(input_mint, output_mint, amount, slippage_bps, session):
    '''Get a quote from the Jupiter API'''
    try:
        url = "https://quote-api.jup.ag/v6/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps,
            'platformFeeBps': 100,
            'prioritizationFeeLamports': 'auto',
        }
        headers = {'Accept': 'application/json'}
        async with session.get(url, params=params, headers=headers) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in get_quote: {e}")
        return None
    

async def get_swap(user_public_key, quote_response, session):
    '''Get swap instructions from the Jupiter API'''
    try:
        fee_token_account = Pubkey.find_program_address(
            [
                b'referral_ata',
                bytes(Pubkey.from_string('3hf1aGtRFdUZtjsej149KTVMsftbv4TRfndtGMJKdVdb')),
                bytes(WRAPPED_SOL_MINT)
            ],
            program_id=Pubkey.from_string('REFER4ZgmyYx9c6He5XfaTMiGfdLwRnkV4RPp9t9iF3')
        )

        url = "https://quote-api.jup.ag/v6/swap"
        payload = json.dumps({
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": True,
            "quoteResponse": quote_response,
            "feeAccount": str(fee_token_account[0])
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        async with session.post(url, data=payload, headers=headers) as response:
            return await response.json()
    except Exception as e:
        print(f"Error in get_swap_instructions: {e}")
        return None
    

async def swap(encrypted_private_key, input_mint, output_mint, amount_lamports, slippage_bps, decimals):
    '''Swap tokens using the Jupiter API'''
    try:    
        # Get a aiohttp session for making API calls
        session = get_session()

        # Decrypt the private key, create a keypair, and get the public key string
        private_key = wallet.decrypt_private_key(encrypted_private_key=encrypted_private_key)
        keypair = Keypair.from_seed(private_key)

        pub_key_str = str(keypair.pubkey())
        
        # Convert the amount to lamports and set it in the transaction
        amount_lamports = int(amount_lamports * (10 ** decimals))


        # Get a quote and swap instructions from the Jupiter API
        quote_response = await get_quote(input_mint, output_mint, amount_lamports, slippage_bps, session)
        if not quote_response:
            print("No quote response.")
            return False
        print(quote_response)
        
        # Get the swap transaction from the Jupiter API
        swap_transaction = await get_swap(pub_key_str, quote_response, session)
        if not swap_transaction:
            print("No swap transaction response.")
            return False
        print(swap_transaction)

        # Sign the transaction, send it to the Solana network, and print the transaction signature
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(swap_transaction['swapTransaction']))

        signature = keypair.sign_message(to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        tx_sig = await client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        print(f"Transaction Signature: {tx_sig.value}")

        return tx_sig.value, quote_response
    except Exception as e:
        print(e)
        return False
    

async def make_swap(db_wallet: SolanaWallet, data: dict, token_data: dict, session: AsyncSession, user_id: int):
    db_user = await session.get(User, user_id)

    if token_data['address'] == data.get('input_mint'):
        slippage = db_user.sell_slippage * 100
    else:
        slippage = db_user.buy_slippage * 100

    response = await swap(
        db_wallet.encrypted_private_key, 
        data.get('input_mint'), 
        data.get('output_mint'),
        data.get('amount'),
        int(slippage),
        data.get('input_decimals')
        )
    
    return response


async def create_swap_in_db(quote_response: dict, wallet_id: int, session: AsyncSession) -> Swap:
    swap_record = Swap(
        wallet=wallet_id,
        input_mint=quote_response['inputMint'],
        output_mint=quote_response['outputMint'],
        input_amount=int(quote_response['inAmount']),
        output_amount=int(quote_response['outAmount']),
        status='Waiting for Confirmation',
        date=datetime.now()
        )
    session.add(swap_record)
    await session.commit()
    return swap_record


def get_data_for_text(token_data: dict, quote_response: dict, data:dict):
    input_decimals = data.get('input_decimals')
    output_decimals = data.get('output_decimals')

    if token_data['address'] == quote_response['inputMint']:
        input_symbol = token_data['symbol'].upper()
        output_symbol = 'SOL'
        trading_points = (float(quote_response['inAmount']) / 10 ** input_decimals) * token_data['price']
    else:
        input_symbol = 'SOL'
        output_symbol = token_data['symbol'].upper()
        trading_points = (float(quote_response['outAmount']) / 10 ** output_decimals) * token_data['price']

    return input_symbol, output_symbol, trading_points



async def end_swap(swap: Swap, db_wallet: SolanaWallet, user_id, trading_points: float, session: AsyncSession):
    swap.status = 'Finalized'
    await session.commit()

    db_wallet.number_of_trades += 1
    db_wallet.trading_points_earned += trading_points
    await user_crud.update_wallet(session, user_id, trading_points)



async def make_swap_with_callback(
        callback_query: CallbackQuery, 
        db_wallet: SolanaWallet, 
        user_id: int,
        token_data: dict,
        data: dict,
        session: AsyncSession,
        state: FSMContext
        ):
    response = await make_swap(db_wallet, data, token_data, session, user_id)
    await callback_query.message.edit_caption(caption='Transaction sent. Waiting for confirmation...')

    try:
        tx_sig, quote_response = response
        swap_record = await create_swap_in_db(quote_response, db_wallet.id, session)

        confirmation = await client.confirm_transaction(tx_sig, commitment=Finalized, sleep_seconds=5)
        if confirmation.value:
            if confirmation.value[0].confirmation_status == TransactionConfirmationStatus.Finalized:
                input_decimals = data.get('input_decimals')
                output_decimals = data.get('output_decimals')

                input_symbol, output_symbol, trading_points = get_data_for_text(token_data, quote_response, data)
                platforms = [swap_info['swapInfo']['label'] for swap_info in quote_response.get('routePlan')]
                text = texts.SUCCESSFULL_TRANSACTION.format(
                        input_symbol=input_symbol, output_symbol=output_symbol,
                        in_amount=float(quote_response['inAmount']) / 10 ** input_decimals,
                        out_amount=float(quote_response['outAmount']) / 10 ** output_decimals,
                        platforms=', '.join(platforms),
                        trading_points=trading_points,
                    )
                await callback_query.message.edit_caption(caption=text, reply_markup=to_home())

                await end_swap(swap_record, db_wallet, user_id, trading_points, session)
                    
                await state.clear()
    except Exception as e:
        await callback_query.message.edit_caption(caption='Transaction failed!', reply_markup=to_home())
        swap_record.status = 'Failed'
        await session.commit()
        print(e)
        await state.clear()
        return
    

async def make_swap_with_message(
    message: CallbackQuery, 
    db_wallet: SolanaWallet, 
    user_id: int,
    token_data: dict,
    data: dict,
    session: AsyncSession,
    ):
    response = await make_swap(db_wallet, data, token_data, session, user_id)
    await message.answer(text='Transaction sent. Waiting for confirmation...')

    try:
        tx_sig, quote_response = response
        swap_record = await create_swap_in_db(quote_response, db_wallet.id, session)

        confirmation = await client.confirm_transaction(tx_sig, commitment=Finalized, sleep_seconds=5)
        if confirmation.value:
            if confirmation.value[0].confirmation_status == TransactionConfirmationStatus.Finalized:
                input_decimals = data.get('input_decimals')
                output_decimals = data.get('output_decimals')


                input_symbol, output_symbol, trading_points = get_data_for_text(token_data, quote_response, data)
                platforms = [swap_info['swapInfo']['label'] for swap_info in quote_response.get('routePlan')]
                text = texts.SUCCESSFULL_TRANSACTION.format(
                        input_symbol=input_symbol, output_symbol=output_symbol,
                        in_amount=float(quote_response['inAmount']) / 10 ** input_decimals,
                        out_amount=float(quote_response['outAmount']) / 10 ** output_decimals,
                        platforms=', '.join(platforms),
                        trading_points=trading_points,
                    )
                await message.answer(text=text, reply_markup=to_home())

                await end_swap(swap_record, db_wallet, user_id, trading_points, session)

                
    except Exception as e:
        await message.answer(text='Transaction failed!', reply_markup=to_home())
        swap_record.status = 'Failed'
        await session.commit()
        print(e)
        return