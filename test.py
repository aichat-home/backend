import asyncio
import json

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore

from solders.system_program import transfer, TransferParams

from sqlalchemy.ext.asyncio import AsyncSession

from models import RefferAccount
from session import get_session, init_session
from utils import wallet
from utils.swap import utils, raydium
from rpc import client


def test(**fields):
    for key, value in fields.items():
        print(f'{key} - {value}')


async def main():
    # init_session()
    # session = get_session()

    # encrypted_private_key = 'gAAAAABnCTssgFveNN5spsh1nHxDOAj0GutFakruX2gkzabvAYl-89NCOzfZwcm2gD1BZ2iWKP1DHV3R1vaBZoTktfmErDTP7kTkxpXJb1h2HMHGYkxfFGHy--FBzYPryi_WvFVDFCpN' 
    # private_key = b'\xe5\tK4\x1d\xc7\x9f]fD\x19\x9dq\xd4]%\xda\x97\x7fP]l1\x17\xb9\xaa1\x0fx\xaf]\xa3'
    # keypair = Keypair.from_seed(private_key)
    test(a=1, b=5)

    # await session.close()


asyncio.run(main())
