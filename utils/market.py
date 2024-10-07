from aiohttp import ClientSession

from cache import simple_cache



async def get_mints(session: ClientSession) -> list[dict]:
    '''Getting a list of mints
    Uses Jupiter API to fetch a list of mints.'''

    mints = simple_cache.get('mints')

    if mints:
        return mints

    async with session.get('https://tokens.jup.ag/tokens?tags=verified') as response:
        mints = await response.json()
    
    simple_cache.set('mints', mints, 3600)  # Cache mints for 1 hour
    return mints


async def get_token_data_by_address(session: ClientSession, address: str, mint: dict | None = None) -> dict:
    '''Getting token data by address
    Uses CoinGecko API to fetch token data.
    '''
    data = simple_cache.get(f'token_data_{address}')
    if data:
        return data
    

    headers = {
        'ccept': 'application/json',
        'x-cg-api-key': 'CG-4NNKcN8uJxitLfGbHiUyvwDS'
    }

    url = f'https://api.coingecko.com/api/v3/coins/solana/contract/{address}'
    
    async with session.get(url, headers=headers) as response:
        data = await response.json()

    if data.get('symbol'):
        if mint:
            data = get_need_data(data, mint)
            simple_cache.set(f'token_data_{address}', data, 600)  # Cache token data for 1 minute
        return data
    elif data.get('status', {}).get('error_code', 200) == 429:
        return -1
    return None


def get_need_data(token_data: dict, mint: dict) -> dict:
    '''Get need data from token data'''

    need_data = {
            'symbol': token_data.get('symbol'),
            'name': token_data.get('name'),
            'image': mint.get('logoURI'),
            'address': mint.get('address'),
            'price': token_data.get('market_data', {}).get('current_price', {}).get('usd'),
            'market_cap': token_data.get('market_data', {}).get('market_cap', {}).get('usd'),
            'total_volume': token_data.get('market_data', {}).get('total_volume', {}).get('usd'),
            'price_change_percentage_24h': token_data.get('market_data', {}).get('price_change_percentage_24h'),
            }
    return need_data



