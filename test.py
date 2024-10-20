import asyncio
from utils import pump
from datetime import datetime, timezone

from solders.pubkey import Pubkey # type: ignore

from session import get_session, init_session
from utils import swap
from spl.token.constants import WRAPPED_SOL_MINT
from rpc import client


async def main():
    init_session()
    session = get_session()
    # print(await pump.get_pump_token_info(session, '4YnTnXGvRV9vLiae6LM7f5FdKssJeDfTic9nzeKEpump'))
    
    response = await client.get_account_info_json_parsed(Pubkey.from_string('95Pb7UEfqx1SyPAZJmfB8BCdZeekf6z16zj2Y8yKG5Jb'))
    print(response.value.data.parsed['info']['decimals'])

    await session.close()


asyncio.run(main())