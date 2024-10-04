from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Task, Account
from db import database
from schemas import TaskCheck
from utils import validate_dependency, user as user_crud, task
from cache import cache_manager



router = APIRouter(tags=['Tasks'])

@router.get('/')
@cache_manager.cache_response(key='tasks', ttl=600)
async def get_tasks(session: AsyncSession = Depends(database.get_async_session)):
    stmt = select(Task)
    result = await session.execute(stmt)
    tasks =  result.scalars().all()

    grouped_tasks = defaultdict(list)
    for task in tasks:
        grouped_tasks[task.type].append(task)

    # Return grouped tasks as dictionary
    dct = {}
    for task_type, tasks in grouped_tasks.items():
        dct[task_type] = [task for task in tasks]
    return dct


@router.post('/check')
async def check_task(
    task_check: TaskCheck,
    session: AsyncSession = Depends(database.get_async_session),
    user: dict = Depends(validate_dependency)
):
    result = await session.execute(select(Account).options(
        selectinload(Account.completedTasks)  # Eager load account
    ).filter(Account.id == user.get('id')))
    account = result.scalars().first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await session.execute(select(Task).filter(Task.id == task_check.task_id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task in account.completedTasks:
        raise HTTPException(status_code=400, detail="Task already completed by this account")

    account.completedTasks.append(task)

    # Update wallet balance
    await user_crud.update_wallet(session, user.get('id'), task.amount)

    return {"completed": True}


@router.post('/check/referral')
async def check_referral(
    count: int, 
    session: AsyncSession = Depends(database.get_async_session),
    user: dict = Depends(validate_dependency)
    ):
    '''
    Check if account has referred a specific number of accounts.
    return {"referral_valid": True} if account have referred a specific number of accounts
    return {"referral_valid": False} if account have not referred a specific number of accounts
    '''
    result = await session.execute(select(Account).options(
        selectinload(Account.reffers)
    ).filter(Account.id == user.get('id')))
    account = result.scalars().first()

    if account:
        if account.reffers_checked < count:
            if len(account.reffers) >= count:
                reward = task.get_reward_for_reffers(count)
                if reward:
                    await user_crud.update_wallet(session, user.get('id'), reward)
                    account.reffers_checked = count
                    await session.commit()
                    return {"referral_valid": True}
        
    return {"referral_valid": False}


