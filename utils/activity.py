from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import DailyActivity



async def get_or_create_daily_activity(session: AsyncSession):
    stmt = select(DailyActivity).filter(DailyActivity.finished == False)
    result = await session.execute(stmt)
    daily_activity = result.scalars().first()

    if daily_activity:
        if datetime.now().day != daily_activity.date.day:
            daily_activity.finished = True
            await session.commit()
            daily_activity = DailyActivity(activity_id=1, date=datetime.now(), finished=False)
            session.add(daily_activity)
            await session.commit()
    else:
        daily_activity = DailyActivity(activity_id=1, date=datetime.now(), finished=False)
        session.add(daily_activity)
        await session.commit()

    return daily_activity


async def update_daily_activity_users_entered(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.users_entered += 1
    await session.commit()
    

async def update_daily_activity_new_users_entered(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.new_users_entered += 1
    await session.commit()


async def update_daily_activity_reffered_users_entered(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.reffered_users_entered += 1
    await session.commit()
    

async def update_daily_activity_connected_wallets(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.connected_wallets += 1
    await session.commit()


async def update_daily_activity_farm_started(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.farm_started += 1
    await session.commit()


async def update_daily_activity_partner_users_created(session: AsyncSession, daily_activity: DailyActivity):
    daily_activity.partner_users_entered += 1
    await session.commit()