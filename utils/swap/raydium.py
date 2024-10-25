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

from rpc import client

from .constants import SOL_DECIMAL, SOL, TOKEN_PROGRAM_ID, UNIT_BUDGET, UNIT_PRICE, WSOL
from .layouts import ACCOUNT_LAYOUT
from .utils import (
    confirm_txn, fetch_pool_keys, 
    get_token_price, make_swap_instruction, 
    get_token_balance, get_swap_and_fee_amount, 
    create_fee_instruction
    )


async def buy(pair_address: str, sol_in: float, slippage: int, payer_keypair: Keypair) -> bool:
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

        token_account_check = await client.get_token_accounts_by_owner(payer_keypair.pubkey(), TokenAccountOpts(mint), Processed)
        if token_account_check.value:
            token_account = token_account_check.value[0].pubkey
            token_account_instr = None
        else:
            token_account = get_associated_token_address(payer_keypair.pubkey(), mint)
            token_account_instr = create_associated_token_account(payer_keypair.pubkey(), payer_keypair.pubkey(), mint)

        wsol_token_account = None
        wsol_account_keypair = None
        create_wsol_account_instr = None
        init_wsol_account_instr = None
        fund_wsol_account_instr = None
        sync_native_instr = None
        wsol_account_check = await client.get_token_accounts_by_owner(payer_keypair.pubkey(), TokenAccountOpts(WSOL), Processed)
        
        if wsol_account_check.value:
            wsol_token_account = wsol_account_check.value[0].pubkey
            
            fund_wsol_account_instr = transfer(
                TransferParams(
                    from_pubkey=payer_keypair.pubkey(),
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
                    from_pubkey=payer_keypair.pubkey(),
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
                    owner=payer_keypair.pubkey()
                )
            )

        swap_instructions = make_swap_instruction(amount_in, minimum_amount_out, wsol_token_account, token_account, pool_keys, payer_keypair)
        fee_instruction = create_fee_instruction(str(payer_keypair.pubkey()), 'F1pVGrtES7xtvmtKZMMxNf7K4asrqyAzLVtc8vHBuELu', fee_amount)

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
        
        if fee_instruction:
            instructions.append(fee_instruction)

        instructions.append(swap_instructions)

        latest_block_hash = await client.get_latest_blockhash()
        compiled_message = MessageV0.try_compile(
            payer_keypair.pubkey(),
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
        }
    
    except Exception as e:
        print('Error:', e)
        return False


async def sell(pair_address: str, amount, slippage, payer_keypair: Keypair):
    try:
        print(f'Pair Address: {pair_address}')

        print('Fetching pool keys...')
        pool_keys = await fetch_pool_keys(pair_address)

        if pool_keys is None:
            print('No pools keys found...')
            return False

        mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != SOL else pool_keys['quote_mint']
        
        token_price, token_decimal = await get_token_price(pool_keys)
        amount_out = float(amount) * float(token_price)
        slippage_adjustment = 1 - (slippage / 100)
        amount_out_with_slippage = amount_out * slippage_adjustment
        minimum_amount_out = int(amount_out_with_slippage * SOL_DECIMAL)
        amount_in = int(amount * (10**token_decimal))

        minimum_amount_out, fee_amount = get_swap_and_fee_amount(minimum_amount_out)

        print(f'Amount In: {amount_in} | Min Amount Out: {minimum_amount_out}')

        token_account = get_associated_token_address(payer_keypair.pubkey(), mint)

        wsol_token_account = None
        wsol_account_keypair = None
        create_wsol_account_instr = None
        init_wsol_account_instr = None
        wsol_account_check = await client.get_token_accounts_by_owner(payer_keypair.pubkey(), TokenAccountOpts(WSOL), Processed)
        
        if wsol_account_check.value:
            wsol_token_account = wsol_account_check.value[0].pubkey

        if wsol_token_account is None:
            wsol_account_keypair = Keypair()
            wsol_token_account = wsol_account_keypair.pubkey()
            
            balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_account(client)

            create_wsol_account_instr = create_account(
                CreateAccountParams(
                    from_pubkey=payer_keypair.pubkey(),
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
                    owner=payer_keypair.pubkey()
                )
            )

        swap_instructions = make_swap_instruction(amount_in, minimum_amount_out, token_account, wsol_token_account, pool_keys, payer_keypair)
        fee_instruction = create_fee_instruction(
            from_pubkey=str(payer_keypair.pubkey()),
            to_pubkey='F1pVGrtES7xtvmtKZMMxNf7K4asrqyAzLVtc8vHBuELu',
            amount=fee_amount
        )

        print('Building transaction...')
        instructions = []
        instructions.append(set_compute_unit_price(UNIT_PRICE))
        instructions.append(set_compute_unit_limit(UNIT_BUDGET))
        
        if create_wsol_account_instr:
            instructions.append(create_wsol_account_instr)
        
        if init_wsol_account_instr:
            instructions.append(init_wsol_account_instr)

        instructions.append(swap_instructions)
        
        instructions.append(fee_instruction)      

        latest_blockhash = await client.get_latest_blockhash()
        compiled_message = MessageV0.try_compile(
            payer_keypair.pubkey(),
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
            'fee_amount': fee_amount / SOL_DECIMAL
        }
    
    except Exception as e:
        print('Error:', e)
        return {'status': 'Failed'}
