from fastapi import APIRouter, Depends

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from schemas import RefferResponse
from utils import validate_dependency, market
from utils.swap.constants import SOL
from session import get_session
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
    client_session = get_session()
    sol_data = await market.get_token_data_by_address(client_session, SOL)
    sol_price = sol_data.get('price', 0)
    response = []

    for referral in referrals:
        response.append(
            {
                'id': referral.id,
                'earned_coins': referral.earned_coins,
                'earned_usd': referral.earned_sol * sol_price,
                'user': referral.user
            }
        )
    return response