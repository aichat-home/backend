import asyncio
import json
import base58
import struct

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore

from solders.system_program import transfer, TransferParams

from sqlalchemy.ext.asyncio import AsyncSession

from models import RefferAccount
from session import get_session, init_session
from utils import wallet, metaplex
from utils.swap import utils, raydium
from rpc import client





async def main():
    # init_session()
    # session = get_session()

    # encrypted_private_key = 'gAAAAABnCTssgFveNN5spsh1nHxDOAj0GutFakruX2gkzabvAYl-89NCOzfZwcm2gD1BZ2iWKP1DHV3R1vaBZoTktfmErDTP7kTkxpXJb1h2HMHGYkxfFGHy--FBzYPryi_WvFVDFCpN' 
    # private_key = b'\xe5\tK4\x1d\xc7\x9f]fD\x19\x9dq\xd4]%\xda\x97\x7fP]l1\x17\xb9\xaa1\x0fx\xaf]\xa3'
    # keypair = Keypair.from_seed(private_key)

    metadata = await metaplex.get_metadata('9nK7shMd2CfWRoWEcMYKqH7KtnhiM3VkJEX5Ep1rpump')
    print(metadata)


    # await session.close()


asyncio.run(main())
