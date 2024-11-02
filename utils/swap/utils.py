import json
import time
import requests
from aiohttp import ClientSession


from .constants import (
    OPEN_BOOK_PROGRAM, 
    RAY_AUTHORITY_V4, 
    RAY_V4, 
    TOKEN_PROGRAM_ID, 
    SOL,
    RAY_CP,
    RAY_VAULT_AUTHORITY
)
from .layouts import (
    LIQUIDITY_STATE_LAYOUT_V4, 
    MARKET_STATE_LAYOUT_V3, 
    SWAP_LAYOUT,
    POOL_STATE_LAYOUT,
    CP_SWAP_LAYOUT
)
from rpc import client


from solana.rpc.commitment import Processed
from solana.rpc.types import TokenAccountOpts
from solana.transaction import AccountMeta, Signature

from solders.instruction import Instruction  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.system_program import TransferParams, transfer



def make_swap_instruction(amount_in:int, minimum_amount_out:int, token_account_in:Pubkey, token_account_out:Pubkey, accounts:dict, owner:Keypair) -> Instruction:
    try:
        keys = [
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['amm_id'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=RAY_AUTHORITY_V4, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['open_orders'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['target_orders'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['base_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['quote_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=OPEN_BOOK_PROGRAM, is_signer=False, is_writable=False), 
            AccountMeta(pubkey=accounts['market_id'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['bids'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['asks'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['event_queue'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['market_base_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['market_quote_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['market_authority'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),  
            AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True), 
            AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False) 
        ]
        
        data = SWAP_LAYOUT.build(
            dict(
                instruction=9,
                amount_in=amount_in,
                min_amount_out=minimum_amount_out
            )
        )
        return Instruction(RAY_V4, data, keys)
    except:
        return None
    

def make_swap_instructions_for_cp(amount_in:int, minimum_amount_out:int, token_account_in:Pubkey, token_account_out:Pubkey, accounts:dict, owner:Keypair) -> Instruction:
    try:
        keys = [
            AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False),
            AccountMeta(pubkey=RAY_VAULT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['amm_config'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['pool_state'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),
            AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['base_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['quote_vault'], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts['base_program'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['quote_program'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['base_mint'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['quote_mint'], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts['observation_key'], is_signer=False, is_writable=True)
        ]

        data = CP_SWAP_LAYOUT.build(
            dict(
                instruction=8,
                amount_in=amount_in,
                min_amount_out=minimum_amount_out
            )
        )
        return Instruction(RAY_CP, data, keys)
    except Exception as e:
        print(e)
        return None


def get_swap_and_fee_amount(amount_in: int) -> tuple[int, int] | None:
    try:
        # Calculate fee amount based on the amount_in
        fee_amount = int(amount_in * (1 / 100))
        # Calculate swap amount considering fee
        swap_amount = amount_in - fee_amount
        return swap_amount, fee_amount
    except Exception as e:
        print(f'Error calculating swap and fee amount {e}')
        return None


def create_fee_instruction(from_pubkey: str, to_pubkey: str, amount: int) -> Instruction | None:
    try:
        fee_instruction = transfer(
            TransferParams(
                from_pubkey=Pubkey.from_string(from_pubkey),
                to_pubkey=Pubkey.from_string(to_pubkey),
                lamports=int(amount)
            )
        )
        return fee_instruction
    except Exception as e:
        print(f'Error creating fee instruction {e}')
        return None


async def fetch_pool_keys(pair_address: str) -> dict:
    try:
        amm_id = Pubkey.from_string(pair_address)
        amm_data = await client.get_account_info_json_parsed(amm_id)
        amm_data = amm_data.value.data
        amm_data_decoded = LIQUIDITY_STATE_LAYOUT_V4.parse(amm_data)
        marketId = Pubkey.from_bytes(amm_data_decoded.serumMarket)
        marketInfo = await client.get_account_info_json_parsed(marketId)
        marketInfo = marketInfo.value.data
        market_decoded = MARKET_STATE_LAYOUT_V3.parse(marketInfo)

        pool_keys = {
            'amm_id': amm_id, 
            'base_mint': Pubkey.from_bytes(market_decoded.base_mint), 
            'quote_mint': Pubkey.from_bytes(market_decoded.quote_mint), 
            'base_decimals': amm_data_decoded.coinDecimals, 
            'quote_decimals': amm_data_decoded.pcDecimals,
            'open_orders': Pubkey.from_bytes(amm_data_decoded.ammOpenOrders),
            'target_orders': Pubkey.from_bytes(amm_data_decoded.ammTargetOrders),
            'base_vault': Pubkey.from_bytes(amm_data_decoded.poolCoinTokenAccount),
            'quote_vault': Pubkey.from_bytes(amm_data_decoded.poolPcTokenAccount),
            'withdrawQueue': Pubkey.from_bytes(amm_data_decoded.poolWithdrawQueue),
            'market_id': marketId,
            'market_authority': Pubkey.create_program_address([bytes(marketId)] + [bytes([market_decoded.vault_signer_nonce])] + [bytes(7)], OPEN_BOOK_PROGRAM), 
            'market_base_vault': Pubkey.from_bytes(market_decoded.base_vault), 
            'market_quote_vault': Pubkey.from_bytes(market_decoded.quote_vault), 
            'bids': Pubkey.from_bytes(market_decoded.bids), 
            'asks': Pubkey.from_bytes(market_decoded.asks),
            'event_queue': Pubkey.from_bytes(market_decoded.event_queue)
        }
        
        return pool_keys
    except Exception as e:
        print(f'Error fetching pool keys: {e}')
        return None


async def fetch_pool_keys_cp(pair_address: str):
    try:
        amm_id = Pubkey.from_string(pair_address)
        amm_data = await client.get_account_info_json_parsed(amm_id)
        amm_data = amm_data.value.data
        amm_data_decoded = POOL_STATE_LAYOUT.parse(amm_data)

        pool_keys = {
            'amm_config': Pubkey.from_bytes(amm_data_decoded.amm_config),
            'pool_state': Pubkey.from_string(pair_address),
            'base_vault': Pubkey.from_bytes(amm_data_decoded.token_0_vault),
            'quote_vault': Pubkey.from_bytes(amm_data_decoded.token_1_vault),
            'base_program': Pubkey.from_bytes(amm_data_decoded.token_0_program),
            'quote_program': Pubkey.from_bytes(amm_data_decoded.token_1_program),
            'base_mint': Pubkey.from_bytes(amm_data_decoded.token_0_mint),
            'quote_mint': Pubkey.from_bytes(amm_data_decoded.token_1_mint),
            'observation_key': Pubkey.from_bytes(amm_data_decoded.observation_key),
            'base_decimals': amm_data_decoded.mint_0_decimals,
            'quote_decimals': amm_data_decoded.mint_1_decimals
        }
        return pool_keys
    except Exception as e:
        print(e)
        return None


async def get_token_balance(mint_str: str, public_key: str):
    try:
        response = await client.get_token_accounts_by_owner_json_parsed(
            Pubkey.from_string(public_key),
            TokenAccountOpts(
                program_id=TOKEN_PROGRAM_ID,
                mint=Pubkey.from_string(mint_str)
            )
        )
        token = response.value[0]
        ui_amount = token.account.data.parsed['info']['tokenAmount']['uiAmount']
        return ui_amount
        
    except Exception as e:
        return None


async def confirm_txn(txn_sig: Signature, max_retries: int = 20, retry_interval: int = 3) -> bool:
    retries = 0
    
    while retries < max_retries:
        try:
            txn_res = await client.get_transaction(txn_sig, encoding='json', commitment='confirmed', max_supported_transaction_version=0)
            txn_json = json.loads(txn_res.value.transaction.meta.to_json())
            
            if txn_json['err'] is None:
                print('Transaction confirmed... try count:', retries)
                return True
            
            print('Error: Transaction not confirmed. Retrying...')
            if txn_json['err']:
                print('Transaction failed.')
                return False
        except Exception as e:
            print('Awaiting confirmation... try count:', retries)
            retries += 1
            time.sleep(retry_interval)
    
    print('Max retries reached. Transaction confirmation failed.')
    return False


async def get_pair_address(mint, client_session: ClientSession):
    url = f'https://api-v3.raydium.io/pools/info/mint?mint1={mint}&poolType=standard&poolSortField=default&sortType=desc&pageSize=1&page=1'
    try:
        async with client_session.get(url) as response:
            response = await response.json()
        pair_address = response['data']['data'][0]['id']
        program_id = response['data']['data'][0]['programId']
        return pair_address, program_id
    except requests.exceptions.RequestException as e:
        print(f'An error occurred: {e}')
        return None


async def get_token_price(pool_keys: dict) -> tuple:
    try:
        # Get vault accounts and decimals
        base_vault = pool_keys['base_vault']
        quote_vault = pool_keys['quote_vault']
        base_decimal = pool_keys['base_decimals']
        quote_decimal = pool_keys['quote_decimals']
        base_mint = pool_keys['base_mint']
        
        # Fetch both token account balances
        balances_response = await client.get_multiple_accounts_json_parsed(
            [base_vault, quote_vault], 
            Processed
        )
        balances = balances_response.value

        # Extract and parse the balances from the JSON-parsed response data
        pool_coin_account = balances[0]
        pool_pc_account = balances[1]

        pool_coin_account_balance = pool_coin_account.data.parsed['info']['tokenAmount']['uiAmount']
        pool_pc_account_balance = pool_pc_account.data.parsed['info']['tokenAmount']['uiAmount']

        # If either balance could not be retrieved, return None
        if pool_coin_account_balance is None or pool_pc_account_balance is None:
            return None, None
        
        # Determine which reserves to use based on whether the coin is SOL or another token
        sol_mint_address = Pubkey.from_string(SOL)
        
        if base_mint == sol_mint_address:
            base_reserve = pool_coin_account_balance
            quote_reserve = pool_pc_account_balance
            token_decimal = quote_decimal
        else:
            base_reserve = pool_pc_account_balance
            quote_reserve = pool_coin_account_balance
            token_decimal = base_decimal
        
        # Calculate the token price based on the reserves
        token_price = base_reserve / quote_reserve
        
        # Return the token price and its decimal places as a tuple
        return token_price, token_decimal

    except Exception as e:
        # Handle any exceptions that occur during execution and return None
        print(f'Error occurred: {e}')
        return None, None   