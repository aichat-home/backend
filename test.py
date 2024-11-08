import asyncio

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore

from utils import wallet


async def main():
    # init_session()
    # session = get_session()

    # encrypted_private_key = 'gAAAAABnCTssgFveNN5spsh1nHxDOAj0GutFakruX2gkzabvAYl-89NCOzfZwcm2gD1BZ2iWKP1DHV3R1vaBZoTktfmErDTP7kTkxpXJb1h2HMHGYkxfFGHy--FBzYPryi_WvFVDFCpN' 
    private_key = b'\xe5\tK4\x1d\xc7\x9f]fD\x19\x9dq\xd4]%\xda\x97\x7fP]l1\x17\xb9\xaa1\x0fx\xaf]\xa3'
    keypair = Keypair.from_seed(private_key)

    # init_session()
    # session = get_session()
    
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

    # token = await wallet.get_token('7PxdDumxtxhaQLLnLdib1fZx6tfznPoaeAQZ8AXv8Bcr', 'BZ1fTDtwXiyK32cLG7dLLmRWyKeghFHLkkiVGuruTvgz')
    # print(token)
    
    # await session.close()

    print(wallet.get_level_for_volume(0.1))


asyncio.run(main())
