from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, BackgroundTasks

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Farm, Reward
from db import database
from utils import validate_dependency, user as user_crud
from core import settings
from background_tasks import tasks


router = APIRouter(tags=['Farm'])



@router.post('/start')
async def start_farm(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(database.get_async_session),
    user: dict = Depends(validate_dependency),
):

    stmt = select(Farm).filter(Farm.wallet == user.get('id')).filter(Farm.status == 'Process')
    result = await session.execute(stmt)

    farm = result.scalars().first()
    
    if not farm:
        background_tasks.add_task(tasks.send_farm_claim_notification, user.get('id'))
        farm = Farm(status='Process', wallet=user.get('id'), created_at=datetime.now())
        session.add(farm) 
        await session.commit()

    reward = await session.get(Reward, user.get('id'))


    total_duration = settings.farm_seconds
    plus_every_second = reward.day * 0.01
    return {
        'plus_every_second': plus_every_second,
        'total_duration': total_duration,
    }


@router.post('/claim')
async def claim_farm(
    session: AsyncSession = Depends(database.get_async_session),
    user: dict = Depends(validate_dependency)
    ):
    user_id = user.get('id')
    time_passed_condition = timedelta(seconds=settings.farm_seconds)

    stmt = select(Farm).filter(Farm.wallet == user_id).filter(Farm.status == 'Process')
    result = await session.execute(stmt)
    farm = result.scalars().first()
    
    if farm:
        if datetime.now() - farm.created_at >= time_passed_condition:
            farm.status = 'Done'
            session.add(farm)
            reward = await session.get(Reward, user.get('id'))
            wallet = await user_crud.update_wallet(session, user_id, reward.day ** 0.01 * settings.farm_seconds)
            await session.commit()
            return {'coins': wallet.coins}