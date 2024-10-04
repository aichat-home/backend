from fastapi import APIRouter, Depends

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Wallet, User
from db import database
from schemas import LeaderboardFullResponse


router = APIRouter(tags=['Leaderboard'])
from utils import user as user_crud, validate_dependency
from cache import simple_cache



@router.get('/', response_model=LeaderboardFullResponse)
async def get_leaderboard(session: AsyncSession = Depends(database.get_async_session), user = Depends(validate_dependency)):
    leaderboard = simple_cache.get('leaderboard')

    if not leaderboard:
        result = await session.execute(
            select(Wallet, User)
            .join(Wallet.user)  # Join Wallet with its related User
            .order_by(Wallet.coins.desc())
            .limit(100)
        )
        
        # Extract the Wallet and User data
        wallets_with_users = result.all()

        # Format the result to include username or first_name along with wallet data
        leaderboard = [
            {
                "id": wallet.id,
                "coins": wallet.coins,
                "username": user.username or user.first_name,  # Use username, or first_name if username is not available
            }
            for wallet, user in wallets_with_users
        ]
        simple_cache.set('leaderboard', leaderboard, ttl=600)  # Cache the leaderboard for 10 minutes

    user_rank = simple_cache.get(f'user_rank_{user.get("id")}')
    if not user_rank:
        user_rank = await user_crud.get_user_rank(session, user.get('id'))
        simple_cache.set(f'user_rank_{user.get("id")}', user_rank, ttl=600)

    return {
        'leaderboard': leaderboard,
        'user_rank': user_rank
        }

