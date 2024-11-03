import asyncio
from aiohttp import ClientSession

from session import get_session, init_session
from rpc import client
from utils.swap.utils import create_fee_instruction
from utils import wallet

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



async def get_quote(session: ClientSession, output_mint: str, amount: float, slippage):
    amount = int(amount * 1_000_000_000)
    async with session.get(f'https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={output_mint}&amount={amount}&slippageBps={int(slippage * 100)}') as response:
        response = await response.json()

    return response


async def get_jupiter_instructions(session: ClientSession, quote: dict, public_key: str):
    data = {
        'quoteResponse': quote,
        'userPublicKey': public_key,
        'wrapAndUnwrapSol': True
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


async def main():
    # init_session()
    # session = get_session()

    # encrypted_private_key = 'gAAAAABnCTssgFveNN5spsh1nHxDOAj0GutFakruX2gkzabvAYl-89NCOzfZwcm2gD1BZ2iWKP1DHV3R1vaBZoTktfmErDTP7kTkxpXJb1h2HMHGYkxfFGHy--FBzYPryi_WvFVDFCpN' 
    private_key = b'\xe5\tK4\x1d\xc7\x9f]fD\x19\x9dq\xd4]%\xda\x97\x7fP]l1\x17\xb9\xaa1\x0fx\xaf]\xa3'
    keypair = Keypair.from_seed(private_key)

    init_session()
    session = get_session()
    
    # public_key = 'F1pVGrtES7xtvmtKZMMxNf7K4asrqyAzLVtc8vHBuELu'
    # output_mint = '2VRbHRxjDxoA6yQhZJqm1Xt2jCtjFa2PVkNWsaQwpump'
    # amount = 0.001

    # quote = await get_quote(session, output_mint, amount, 5)
    # print(quote)
    # jupiter_instructions = await get_jupiter_instructions(session, quote, public_key)
    # tables_accounts = await get_address_lookup_table_accounts(jupiter_instructions['addressLookupTableAddresses'])
    
    # instructions = deserialize_all_instructions(jupiter_instructions)

    # for _ in range(10):
    #     fee_instruction = create_fee_instruction(public_key, public_key, 0.0001 * 1_000_000_000)
    #     instructions.append(fee_instruction)

    # latest_block_hash = await client.get_latest_blockhash()
    # compiled_message = MessageV0.try_compile(
    #         Pubkey.from_string(public_key),
    #         instructions,
    #         tables_accounts,
    #         latest_block_hash.value.blockhash,
    #     )
    # txn = VersionedTransaction(compiled_message, [keypair])
    # txn_sig = await client.send_transaction(txn, opts=TxOpts(skip_preflight=True))
    # txn_sig = txn_sig.value
    # print(txn_sig)

    token = await wallet.get_token('7PxdDumxtxhaQLLnLdib1fZx6tfznPoaeAQZ8AXv8Bcr', 'BZ1fTDtwXiyK32cLG7dLLmRWyKeghFHLkkiVGuruTvgz')
    print(token)
    await session.close()


asyncio.run(main())
