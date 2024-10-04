from fastapi import APIRouter, Depends

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from schemas import RefferResponse
from utils import validate_dependency
from models import RefferAccount
from db import database



router = APIRouter(tags=['Refferals'])

@router.get('/', response_model=list[RefferResponse])
async def get_reffers(session: AsyncSession = Depends(database.get_async_session), user = Depends(validate_dependency)):
    result = await session.execute(
        select(RefferAccount)
        .join(RefferAccount.user)  # Join RefferAccount with its related User
        .filter(RefferAccount.oneWhoInvited == user.get('id'))  # Filtering by the ID of the one who invited
        .options(joinedload(RefferAccount.user))  # Eager loading the user relationship
    )

    # Fetch all referred accounts
    referrals = result.scalars().all()
    return referrals