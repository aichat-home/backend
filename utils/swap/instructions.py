from .utils import fetch_pool_keys, make_swap_instruction, get_token_price
from . import jupiter

from .constants import (
    TOKEN_PROGRAM_ID, 
    SOL,
    WSOL,
    SOL_DECIMAL,
    UNIT_PRICE,
    UNIT_BUDGET
)
from .layouts import ACCOUNT_LAYOUT
from rpc import client
from session import get_session

from sqlalchemy.ext.asyncio import AsyncSession

from solana.rpc.commitment import Processed
from solana.rpc.types import TokenAccountOpts
from solana.rpc.types import TxOpts

from solders.instruction import Instruction  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.system_program import TransferParams, transfer
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price  # type: ignore
from solders.system_program import CreateAccountParams, TransferParams, create_account, transfer
from solders.transaction import VersionedTransaction # type: ignore
from solders.message import MessageV0 # type: ignore

from spl.token.async_client import AsyncToken
from spl.token.instructions import (
    InitializeAccountParams,
    SyncNativeParams,
    create_associated_token_account,
    get_associated_token_address,
    initialize_account,
    sync_native,
    close_account,
    CloseAccountParams
)
from spl.token.constants import TOKEN_PROGRAM_ID



async def make_buy_instruction_for_raydium(pair_address: str, amount_in: str, slippage: float, payer_keypair: Keypair):
    pool_keys = await fetch_pool_keys(pair_address)

    if pool_keys is None:
        return None
        
    mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != SOL else pool_keys['quote_mint']
        
    token_price, token_decimal = await get_token_price(pool_keys)
    amount_out = float(amount_in / SOL_DECIMAL) / float(token_price)
    slippage_adjustment = 1 - (slippage / 100)
    amount_out_with_slippage = amount_out * slippage_adjustment
    minimum_amount_out = int(amount_out_with_slippage * 10 ** token_decimal)

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
    swap_instructions = make_swap_instruction(int(amount_in), int(minimum_amount_out), wsol_token_account, token_account, pool_keys, payer_keypair)
    print(swap_instructions)

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

    instructions.append(swap_instructions)
    
    close_wsol_account_instr = close_account(CloseAccountParams(TOKEN_PROGRAM_ID, wsol_token_account, payer_keypair.pubkey(), payer_keypair.pubkey()))
    instructions.append(close_wsol_account_instr)

    return {
        'instructions': instructions,
        'amount_in': amount_in,
        'minimum_amount_out': minimum_amount_out,
        'wsol_account_keypair': wsol_account_keypair,
        'token_decimal': token_decimal
        }


async def make_sell_instructions_for_raydium(pair_address: str, amount: int, slippage: float, payer_keypair: Keypair):
    pool_keys = await fetch_pool_keys(pair_address)

    if pool_keys is None:
        return None
    
    public_key = payer_keypair.pubkey()

    mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != SOL else pool_keys['quote_mint']
    
    token_price, token_decimal = await get_token_price(pool_keys)
    amount_out = amount * float(token_price)
    slippage_adjustment = 1 - (slippage / 100)
    amount_out_with_slippage = amount_out * slippage_adjustment
    minimum_amount_out = int(amount_out_with_slippage * SOL_DECIMAL)
    amount_in = int(amount * 10 ** token_decimal)

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
    instructions = []
    instructions.append(set_compute_unit_price(UNIT_PRICE))
    instructions.append(set_compute_unit_limit(UNIT_BUDGET))
    
    if create_wsol_account_instr:
        instructions.append(create_wsol_account_instr)
    
    if init_wsol_account_instr:
        instructions.append(init_wsol_account_instr)

    instructions.append(swap_instructions)

    close_wsol_account_instr = close_account(CloseAccountParams(TOKEN_PROGRAM_ID, wsol_token_account, payer_keypair.pubkey(), payer_keypair.pubkey()))
    instructions.append(close_wsol_account_instr)

    return {
        'instructions': instructions,
        'amount_in': amount_in,
        'minimum_amount_out': minimum_amount_out,
        'token_decimal': token_decimal,
        'wsol_account_keypair': wsol_account_keypair
    }



async def make_swap_instructions_for_jupiter(input_mint: str, output_mint: str, amount: int, slippage: float, payer_keypair: Keypair):
    public_key = payer_keypair.pubkey()
    client_session = get_session()
    quote = await jupiter.get_quote(client_session, input_mint, output_mint, amount, slippage)
    jupiter_instructions = await jupiter.get_jupiter_instructions(client_session, quote, str(public_key))
    print(jupiter_instructions)
    tables_accounts = await jupiter.get_address_lookup_table_accounts(jupiter_instructions['addressLookupTableAddresses'])
    
    instructions = jupiter.deserialize_all_instructions(jupiter_instructions)

    return {
        'instructions': instructions,
        'amount_in': int(quote['inAmount']),
        'minimum_amount_out': int(quote['outAmount']),
        'tables_accounts': tables_accounts
        }