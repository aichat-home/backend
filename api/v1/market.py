from enum import Enum

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from utils import market
from session import get_session
from schemas import TokenResponse
from session import get_session



router = APIRouter(tags=['Market'])


class SortBy(Enum):
    total_volume = 'total_volume'
    market_cap = 'market_cap'
    price = 'price'
    price_change_percentage_24h = 'price_change_percentage_24h'


class Sort(Enum):
    asc = 'asc'
    desc = 'desc'


@router.get('/popular', response_model=list[TokenResponse])
async def get_popular_coins(sort_by: SortBy = SortBy.total_volume, sort: Sort = Sort.desc):
    reverse = True if sort == Sort.desc else False

    session = await get_session()
    mints = await market.get_mints(session=session)

    tokens_info = []
    tokens_get = 0
    tokens_tried = 0
    while tokens_get < 10:
        mint = mints[tokens_tried]
        token_data = await market.get_token_data_by_address(session=session, address=mint['address'], mint=mint)
        if token_data == -1:
            tokens_info.sort(key=lambda x: x[sort_by.value], reverse=reverse)
            return tokens_info
        
        if token_data:
            tokens_info.append(token_data)
            tokens_get += 1
        tokens_tried += 1
    
    tokens_info.sort(key=lambda x: x[sort_by.value], reverse=reverse)

    return tokens_info



@router.get('/tokens/search')
async def search_token_by_symbol(q: str):
    session = await get_session()
    mints = await market.get_mints(session=session)
    filtered_tokens = [mint for mint in mints if q.lower() in mint['symbol'].lower()]
    return filtered_tokens
