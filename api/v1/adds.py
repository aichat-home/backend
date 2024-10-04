from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import database
from models.adds import Add
from schemas import AddCreate, AddResponse
from cache import cache_manager


router = APIRouter(tags=['Add'])


@router.get('/', response_model=List[AddResponse])
@cache_manager.cache_response(key='add', ttl=600)
async def get_all_adds(session: AsyncSession = Depends(database.get_async_session)):
    stmt = select(Add)
    result = await session.execute(stmt)

    adds = result.scalars().all()

    return adds
