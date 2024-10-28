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

from ..market import get_token_data_by_address
from .constants import SOL_DECIMAL, SOL, TOKEN_PROGRAM_ID, UNIT_BUDGET, UNIT_PRICE, WSOL
from .commisions import get_all_instructions_for_referrals, get_layer_for_amount
from .layouts import ACCOUNT_LAYOUT
from .utils import (
    fetch_pool_keys, get_token_price, 
    make_swap_instruction, get_swap_and_fee_amount, 
    create_fee_instruction
    )


async def buy(pair_address: str, sol_in: float, slippage: int, payer_keypair: Keypair, user_id: int, session: AsyncSession):
    try:
        print(f'Pair Address: {pair_address}')
        
        print('Fetching pool keys...')
        pool_keys = await fetch_pool_keys(pair_address)

        if pool_keys is None:
            print('No pool keys found...')
            return False

        mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != SOL else pool_keys['quote_mint']
        
        amount_in = int(sol_in * SOL_DECIMAL)
        amount_in, fee_amount = get_swap_and_fee_amount(amount_in=amount_in)
        token_price, token_decimal = await get_token_price(pool_keys)
        amount_out = float(amount_in / SOL_DECIMAL) / float(token_price)
        slippage_adjustment = 1 - (slippage / 100)
        amount_out_with_slippage = amount_out * slippage_adjustment
        minimum_amount_out = int(amount_out_with_slippage * 10 ** token_decimal)
        print(f'Amount In: {amount_in} | Min Amount Out: {minimum_amount_out} | Fee amount {fee_amount}')

        public_key = payer_keypair.pubkey()

        token_account_check = await client.get_token_accounts_by_owner(public_key, TokenAccountOpts(mint), Processed)
        if token_account_check.value:
            token_account = token_account_check.value[0].pubkey
            token_account_instr = None
        else:
            token_account = get_associated_token_address(public_key, mint)
            token_account_instr = create_associated_token_account(public_key, public_key, mint)

        wsol_token_account = None
        wsol_account_keypair = None
        create_wsol_account_instr = None
        init_wsol_account_instr = None
        fund_wsol_account_instr = None
        sync_native_instr = None
        wsol_account_check = await client.get_token_accounts_by_owner(public_key, TokenAccountOpts(WSOL), Processed)
        
        if wsol_account_check.value:
            wsol_token_account = wsol_account_check.value[0].pubkey
            
            fund_wsol_account_instr = transfer(
                TransferParams(
                    from_pubkey=public_key,
                    to_pubkey=wsol_token_account,
                    lamports=int(amount_in)
                )
            )
            sync_native_instr = sync_native(SyncNativeParams(TOKEN_PROGRAM_ID, wsol_token_account))

        if wsol_token_account is None:
            wsol_account_keypair = Keypair()
            wsol_token_account = wsol_account_keypair.pubkey()
            
            balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_account(client)

            create_wsol_account_instr = create_account(
                CreateAccountParams(
                    from_pubkey=public_key,
                    to_pubkey=wsol_token_account,
                    lamports=int(balance_needed + amount_in),
                    space=ACCOUNT_LAYOUT.sizeof(),
                    owner=TOKEN_PROGRAM_ID,
                )
            )

            init_wsol_account_instr = initialize_account(
                InitializeAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    mint=WSOL,
                    owner=public_key
                )
            )

        swap_instructions = make_swap_instruction(amount_in, minimum_amount_out, wsol_token_account, token_account, pool_keys, payer_keypair)

        client_session = get_session()
        sol_data = await get_token_data_by_address(client_session, SOL)
        print(f'Sol data {sol_data}')
        price = sol_data['price']
        
        layers = get_layer_for_amount(price * sol_in)
        print(f'Layer: {layers}')
        comission_instructions, referral_amount_fee, result = None, 0, {}
        if layers:
            comission_instructions, referral_amount_fee = await get_all_instructions_for_referrals(user_id, str(public_key), fee_amount, layers, session)
            print(comission_instructions, referral_amount_fee)

        print('Building transaction...')
                
        instructions = []
        instructions.append(set_compute_unit_price(UNIT_PRICE))
        instructions.append(set_compute_unit_limit(UNIT_BUDGET))

        if create_wsol_account_instr:
            instructions.append(create_wsol_account_instr)

        if init_wsol_account_instr:
            instructions.append(init_wsol_account_instr)

        if fund_wsol_account_instr:
            instructions.append(fund_wsol_account_instr)
            
        if sync_native_instr:
            instructions.append(sync_native_instr)
        
        if token_account_instr:
            instructions.append(token_account_instr)
        
        if comission_instructions:
            for comission_instruction in comission_instructions:
                instructions.append(comission_instruction)

        platform_fee_instruction = create_fee_instruction(from_pubkey=str(public_key), to_pubkey=settings.admin_wallet_address, amount=fee_amount - referral_amount_fee)
        instructions.append(platform_fee_instruction)
        instructions.append(swap_instructions)

        latest_block_hash = await client.get_latest_blockhash()
        compiled_message = MessageV0.try_compile(
            public_key,
            instructions,
            [],
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
            'amount_in': amount_in / SOL_DECIMAL,
            'fee_amount': fee_amount / SOL_DECIMAL,
            'minimum_amount_out': amount_out,
            'token_decimal': token_decimal,
            'txn_sig': txn_sig,
            'result': result
        }
    
    except Exception as e:
        print('Error:', e)
        return False


async def sell(pair_address: str, amount, slippage, payer_keypair: Keypair, user_id: int, session: AsyncSession):
    try:
        print(f'Pair Address: {pair_address}')

        print('Fetching pool keys...')
        pool_keys = await fetch_pool_keys(pair_address)

        if pool_keys is None:
            print('No pools keys found...')
            return False
        
        public_key = payer_keypair.pubkey()

        mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != SOL else pool_keys['quote_mint']
        
        token_price, token_decimal = await get_token_price(pool_keys)
        amount_out = float(amount) * float(token_price)
        slippage_adjustment = 1 - (slippage / 100)
        amount_out_with_slippage = amount_out * slippage_adjustment
        minimum_amount_out = int(amount_out_with_slippage * SOL_DECIMAL)
        amount_in = int(amount * (10**token_decimal))

        minimum_amount_out, fee_amount = get_swap_and_fee_amount(minimum_amount_out)

        print(f'Amount In: {amount_in} | Min Amount Out: {minimum_amount_out}')

        token_account = get_associated_token_address(public_key, mint)

        wsol_token_account = None
        wsol_account_keypair = None
        create_wsol_account_instr = None
        init_wsol_account_instr = None
        wsol_account_check = await client.get_token_accounts_by_owner(public_key, TokenAccountOpts(WSOL), Processed)
        
        if wsol_account_check.value:
            wsol_token_account = wsol_account_check.value[0].pubkey

        if wsol_token_account is None:
            wsol_account_keypair = Keypair()
            wsol_token_account = wsol_account_keypair.pubkey()
            
            balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_account(client)

            create_wsol_account_instr = create_account(
                CreateAccountParams(
                    from_pubkey=public_key,
                    to_pubkey=wsol_token_account,
                    lamports=int(balance_needed),
                    space=ACCOUNT_LAYOUT.sizeof(),
                    owner=TOKEN_PROGRAM_ID,
                )
            )

            init_wsol_account_instr = initialize_account(
                InitializeAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    mint=WSOL,
                    owner=public_key
                )
            )

        swap_instructions = make_swap_instruction(amount_in, minimum_amount_out, token_account, wsol_token_account, pool_keys, payer_keypair)

        client_session = get_session()
        sol_data = await get_token_data_by_address(client_session, SOL)
        price = sol_data['price']
        
        layers = get_layer_for_amount(price * amount_out)
        comission_instructions, referral_amount_fee, result = None, 0, {}
        if layers:
            comission_instructions, referral_amount_fee = await get_all_instructions_for_referrals(user_id, str(public_key), fee_amount, layers, session)
            print(comission_instructions, referral_amount_fee)

        print('Building transaction...')
        instructions = []
        instructions.append(set_compute_unit_price(UNIT_PRICE))
        instructions.append(set_compute_unit_limit(UNIT_BUDGET))
        
        if create_wsol_account_instr:
            instructions.append(create_wsol_account_instr)
        
        if init_wsol_account_instr:
            instructions.append(init_wsol_account_instr)

        instructions.append(swap_instructions)
        
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
            'token_in': amount,
            'sol_out': amount_out,
            'txn_sig': txn_sig,
            'token_decimal': token_decimal,
            'fee_amount': fee_amount / SOL_DECIMAL,
            'result': result
        }
    
    except Exception as e:
        print('Error:', e)
        return {'status': 'Failed'}
