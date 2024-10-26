from aiohttp import ClientSession
from solana.rpc.async_api import AsyncClient

from solders.pubkey import Pubkey # type: ignore

from cache import simple_cache
from rpc import client


async def get_mints(session: ClientSession) -> dict:
    '''Getting a list of mints
    Uses Jupiter API to fetch a list of mints.'''

    mints = simple_cache.get('mints')

    if mints:
        return mints

    async with session.get('https://tokens.jup.ag/tokens?tags=verified') as response:
        mints = await response.json()
    
    simple_cache.set('mints', mints, 600)  # Cache mints for 10 minutes
    return mints


def get_token_symbol(mint_to_search, mints):
    '''Getting token symbol by mint'''
    for mint in mints:
        if mint['address'] == mint_to_search:
            return mint


async def get_token_data_by_address(session: ClientSession, address: str) -> dict:
    '''Getting token data by address
    Uses Dexscreen API to fetch token data.
    '''
    data = simple_cache.get(f'token_data_{address}')
    if data:
        return data

    url = f'https://api.dexscreener.com/latest/dex/tokens/{address}'
    
    async with session.get(url) as response:
        data = await response.json()


    if data.get('pairs'):
        pair = data.get('pairs')[0]
        token_data = get_need_data_from_pair(pair)
        token_data['address'] = address
        simple_cache.set(f'token_data_{address}', token_data, 10)
        return token_data
    
    # data = await pump.get_pump_token_info(session, address)
    # if data:
    #     return data

    return None


async def get_token_decimals(address: str):
    '''Getting token decimals by address
    Uses Solana RPC to fetch token decimals.
    '''
    decimals = simple_cache.get(f'token_decimals_{address}')
    if decimals:
        return decimals
    
    response = await client.get_account_info_json_parsed(Pubkey.from_string('95Pb7UEfqx1SyPAZJmfB8BCdZeekf6z16zj2Y8yKG5Jb'))
    if response:
        decimals = response.value.data.parsed['info']['decimals']
        simple_cache.set(f'token_decimals_{address}', decimals, 3600)
        return decimals


def get_need_data_from_pair(pair: dict):
    base_token = pair.get('baseToken', {})
    name = base_token.get('name', '')
    symbol = base_token.get('symbol', '')
    price_usd = pair.get('priceUsd', 0)
    price_change = pair.get('priceChange', {})
    m5 = price_change.get('m5', 0)
    h1 = price_change.get('h1', 0)
    h6 = price_change.get('h6', 0)
    h24 = price_change.get('h24', 0)
    liquidity = pair.get('liquidity', {}).get('quote')
    mcap = pair.get('marketCap', 0)

    return {
            'name': name,
            'symbol': symbol,
            'price': float(price_usd),
            'm5': m5,
            'h1': h1,
            'h6': h6,
            'h24': h24,
            'liquidity': liquidity,
            'market_cap': mcap,
        }


def format_number(num):
    if num >= 1_000_000_000:  # Billions
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:  # Millions
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:  # Thousands
        return f"{num / 1_000:.2f}K"
    else:
        return str(num)  # Return as is if less than 1000