import asyncio
from aiohttp import ClientSession

from session import get_session, init_session
from rpc import client
from utils.swap.utils import create_fee_instruction

import base64
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solders.instruction import Instruction, AccountMeta # type: ignore
from solders.message import  to_bytes_versioned # type: ignore
from solders.keypair import Keypair # type: ignore
from solders.transaction import VersionedTransaction # type: ignore
from solders.message import MessageV0 # type: ignore
from solders.address_lookup_table_account import AddressLookupTableAccount, AddressLookupTable # type: ignore

from solana.rpc.commitment import Processed, Finalized
from solana.rpc.types import TxOpts




async def get_address_lookup_table_accounts(keys):
    try:
        if keys:
            tasks = [
                get_account_info(key) for key in keys
            ]
            address_lookup_tables = await asyncio.gather(*tasks)
            # Filter out accounts with no state
            address_lookup_tables = [table for table in address_lookup_tables if table['state'] is not None]
            address_lookup_table_accounts = []
            for address_lookup_table in address_lookup_tables:
                address_lookup_table_accounts.append(AddressLookupTableAccount(
                    key=address_lookup_table['key'],
                    addresses=address_lookup_table['state'].addresses
                ))
            return address_lookup_table_accounts
        return []
    except Exception as e:
        print(e)
        return []


async def get_account_info(key):
    account_info = await client.get_account_info(Pubkey.from_string(key))
    if account_info.value is not None:
        state = AddressLookupTable.deserialize(account_info.value.data)
        return {'key': Pubkey.from_string(key), 'state': state}
    else:
        return {'key': Pubkey.from_string(key), 'state': None}



async def get_quote(session: ClientSession, input_mint: str, output_mint: str, amount: int, slippage: int):
    async with session.get(f'https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={int(slippage * 100)}') as response:
        response = await response.json()

    return response


async def get_jupiter_instructions(session: ClientSession, quote: dict, public_key: str):
    data = {
        'quoteResponse': quote,
        'userPublicKey': public_key,
        'wrapAndUnwrapSol': True,
        'prioritizationFeeLamports': 'auto',
        'dynamicComputeUnitLimit': True
    }
    headers = {
      'Content-Type': 'application/json'
    }
    async with session.post('https://quote-api.jup.ag/v6/swap-instructions', headers=headers, json=data) as response:
        response = await response.json()
    
    return response


def deserialize_instructions(instruction: dict):
    try:
        return Instruction(
            program_id=Pubkey.from_string(instruction['programId']),
            data=base64.b64decode(instruction['data']),
            accounts=[AccountMeta(
                pubkey=Pubkey.from_string(account['pubkey']),
                is_signer=account['isSigner'],
                is_writable=account['isWritable']
            ) for account in instruction['accounts']]
        )
    except Exception as e:
        print(e)
        return None


def deserialize_all_instructions(data: dict):
    deserialized_instructions = []
    
    # Collect all instructions from the dictionary, handling both lists and single dictionaries
    instructions = []
    for value in data.values():
        if isinstance(value, list):  # If it's a list of instructions
            instructions.extend(value)
        elif isinstance(value, dict):  # If it's a single instruction
            instructions.append(value)

    # Deserialize each collected instruction
    for instruction in instructions:
        deserialized = deserialize_instructions(instruction)
        if deserialized:
            deserialized_instructions.append(deserialized)

    return deserialized_instructions
