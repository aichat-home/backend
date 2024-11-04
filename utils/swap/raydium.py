from solana.rpc.commitment import Processed
from solana.rpc.types import TokenAccountOpts, TxOpts

from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solders.system_program import CreateAccountParams, TransferParams, create_account, transfer
from solders.transaction import VersionedTransaction  # type: ignore
from solders.message import MessageV0  # type: ignore

from spl.token.async_client import AsyncToken
from spl.token.instructions import (
    InitializeAccountParams,
    SyncNativeParams,
    create_associated_token_account,
    get_associated_token_address,
    initialize_account,
    sync_native,
)

from sqlalchemy.ext.asyncio import AsyncSession

from rpc import client
from session import get_session
from core import settings
from utils import market

from ..market import get_token_data_by_address
from .constants import SOL_DECIMAL, SOL, TOKEN_PROGRAM_ID, UNIT_BUDGET, UNIT_PRICE, WSOL, RAY_V4, RAY_CP
from .commisions import get_all_instructions_for_referrals, get_layer_for_amount
from .layouts import ACCOUNT_LAYOUT
from .utils import (
    fetch_pool_keys, get_token_price, 
    make_swap_instruction, get_swap_and_fee_amount, 
    create_fee_instruction, fetch_pool_keys_cp,
    make_swap_instructions_for_cp, get_pair_address
    )
from .instructions import make_buy_instruction_for_raydium, make_sell_instructions_for_raydium, make_swap_instructions_for_jupiter



async def buy(output_mint: str, sol_in: float, slippage: float, payer_keypair: Keypair, user_id: int, session: AsyncSession):
    try:
        client_session = get_session()
        pair_address, program_id = await get_pair_address(output_mint, client_session)

        print(f'Pair Address: {pair_address}')
        public_key = payer_keypair.pubkey()
        
        amount_in = sol_in * SOL_DECIMAL
        amount_in, fee_amount = get_swap_and_fee_amount(amount_in)
        if program_id == str(RAY_V4):
            instructions_data = await make_buy_instruction_for_raydium(pair_address, amount_in, slippage, payer_keypair)
        else:
            instructions_data = await make_swap_instructions_for_jupiter(SOL, output_mint, int(amount_in), slippage, payer_keypair)
        instructions = instructions_data['instructions']
        wsol_account_keypair = instructions_data.get('wsol_account_keypair')
        token_decimal = instructions_data.get('token_decimal')
        amount_out = instructions_data['minimum_amount_out']
        tables_accounts = instructions_data.get('tables_accounts', [])

        if token_decimal is None:
            token_decimal = await market.get_token_decimals(output_mint)

        sol_data = await get_token_data_by_address(client_session, SOL)
        print(f'Sol data {sol_data}')
        price = sol_data['price']
        
        layers = get_layer_for_amount(price * sol_in)
        print(f'Layer: {layers}')
        comission_instructions, referral_amount_fee, result = None, 0, {}
        if layers:
            comission_instructions, referral_amount_fee, result = await get_all_instructions_for_referrals(user_id, str(public_key), fee_amount, layers, session)
            print(comission_instructions, referral_amount_fee)

        print('Building transaction...')
                
        
        if comission_instructions:
            for comission_instruction in comission_instructions:
                instructions.append(comission_instruction)

        platform_fee_instruction = create_fee_instruction(from_pubkey=str(public_key), to_pubkey=settings.admin_wallet_address, amount=fee_amount - referral_amount_fee)
        instructions.append(platform_fee_instruction)

        latest_block_hash = await client.get_latest_blockhash()
        compiled_message = MessageV0.try_compile(
            public_key,
            instructions,
            tables_accounts,
            latest_block_hash.value.blockhash,
        )

        if wsol_account_keypair:
            txn = VersionedTransaction(compiled_message, [payer_keypair, wsol_account_keypair])
        else:
            txn = VersionedTransaction(compiled_message, [payer_keypair])
        
        txn_sig = await client.send_transaction(txn, opts=TxOpts(skip_preflight=True))
        txn_sig = txn_sig.value
        
        print('Transaction Signature', txn_sig)
        return {
            'status': 'Confirmed',
            'amount_in': amount_in,
            'fee_amount': fee_amount,
            'minimum_amount_out': amount_out,
            'token_decimal': token_decimal,
            'txn_sig': txn_sig,
            'sol_price': sol_data['price'],
            'result': result
        }
    
    except Exception as e:
        print('Error:', e)
        return False


async def sell(input_mint: str, amount, slippage, payer_keypair: Keypair, user_id: int, token_decimal: int, session: AsyncSession):
    try:
        public_key = payer_keypair.pubkey()
        client_session = get_session()
        pair_address, program_id = await get_pair_address(input_mint, client_session)

        print(f'Pair Address: {pair_address}')

        if program_id == str(RAY_V4):
            instruction_data = await make_sell_instructions_for_raydium(pair_address, amount, slippage, payer_keypair)
        else:
            instruction_data = await make_swap_instructions_for_jupiter(input_mint, SOL, int(amount * 10 ** token_decimal), slippage, payer_keypair)
        instructions = instruction_data['instructions']
        amount_out = instruction_data['minimum_amount_out']
        amount_out_ui = instruction_data['minimum_amount_out'] / SOL_DECIMAL
        fee_amount = int(amount_out * (settings.program_fee_percentage / 100))
        wsol_account_keypair = instruction_data.get('wsol_account_keypair')

        sol_data = await get_token_data_by_address(client_session, SOL)
        price = sol_data['price']
        
        print(price * amount_out_ui)
        layers = get_layer_for_amount(price * amount_out_ui)
        comission_instructions, referral_amount_fee, result = None, 0, {}
        if layers:
            comission_instructions, referral_amount_fee, result = await get_all_instructions_for_referrals(user_id, str(public_key), fee_amount, layers, session)
            print(comission_instructions, referral_amount_fee)

        print('Building transaction...')
        
        
        if comission_instructions:
            for comission_instruction in comission_instructions:
                instructions.append(comission_instruction)

        platform_fee_instruction = create_fee_instruction(from_pubkey=str(public_key), to_pubkey=settings.admin_wallet_address, amount=fee_amount - referral_amount_fee)
        instructions.append(platform_fee_instruction)    

        latest_blockhash = await client.get_latest_blockhash()
        compiled_message = MessageV0.try_compile(
            public_key,
            instructions,
            [],  
            latest_blockhash.value.blockhash,
        )

        if wsol_account_keypair:
            txn = VersionedTransaction(compiled_message, [payer_keypair, wsol_account_keypair])
            txn_sig = await client.send_transaction(txn, opts=TxOpts(skip_preflight=True))
        else:
            txn = VersionedTransaction(compiled_message, [payer_keypair])
            txn_sig = await client.send_transaction(txn, opts=TxOpts(skip_preflight=True))
        txn_sig = txn_sig.value
        
        print('Transaction Signature', txn_sig)
        return {
            'status': 'Confirmed',
            'token_in': amount * 10 ** token_decimal,
            'sol_out': amount_out,
            'txn_sig': txn_sig,
            'token_decimal': token_decimal,
            'fee_amount': fee_amount / SOL_DECIMAL,
            'sol_price': sol_data['price'],
            'result': result
        }
    
    except Exception as e:
        print('Error:', e)
        return {'status': 'Failed'}
