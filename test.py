import asyncio
import json

from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore

from session import get_session, init_session
from utils import wallet
from utils.swap import utils, raydium
from rpc import client


async def main():
    init_session()
    session = get_session()

    # encrypted_private_key = 'gAAAAABnCTssgFveNN5spsh1nHxDOAj0GutFakruX2gkzabvAYl-89NCOzfZwcm2gD1BZ2iWKP1DHV3R1vaBZoTktfmErDTP7kTkxpXJb1h2HMHGYkxfFGHy--FBzYPryi_WvFVDFCpN' 
    # private_key = wallet.decrypt_private_key(encrypted_private_key=encrypted_private_key)
    # print(private_key)
    # keypair = Keypair.from_seed(private_key)
    devnet_url = "https://api.devnet.solana.com"

    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "DDg4VmQaJV9ogWce7LpcjBA9bv22wRp5uaTPa5pGjijF",
            {"encoding": "jsonParsed"}
        ]
    }
    async with session.post(devnet_url, data=json.dumps(params), headers={"Content-Type": "application/json"}) as response:
         response = await response.json()

    result = response.get("result", [])
    if result:
        for account in result:
            print(f"Pool account: {account['pubkey']}")
    

    pool_keys = await utils.fetch_pool_keys('AjQmELzXAYjhGeCxAqrUfJdvh8BBeKmUiaoLaA5gPWaq')    


    await session.close()


asyncio.run(main())
# import requests
# import json

# try:
#         devnet_url = "https://api.devnet.solana.com"

#         params = {
#             "jsonrpc": "2.0",
#             "id": 1,
#             "method": "getProgramAccounts",
#             "params": [
#                 "DDg4VmQaJV9ogWce7LpcjBA9bv22wRp5uaTPa5pGjijF",
#                 {"encoding": "jsonParsed"}
#             ]
#         }

#         response = requests.post(devnet_url, headers={"Content-Type": "application/json"}, data=json.dumps(params))

#         if response.status_code == 200:
#             result = response.json().get("result", [])
#             if result:
#                 for account in result:
#                     print(f"Pool account: {account['pubkey']}")
# except Exception as err:
#     print(err)
