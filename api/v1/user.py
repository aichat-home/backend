from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from utils import (
    user as user_crud,
    validate_dependency,
    check_streak,
    already_claimed_today,
    get_plus_every_second_for_day,
    get_rewards,
    task,
    activity,
    wallet
)

from schemas import UserCreate, UserCreateBody, GetOrCreate, SaveWallet
from db import database
from models import User, Reward, Wallet
from core import settings


router = APIRouter(tags=["User"])


@router.post("/get-or-create", response_model=GetOrCreate)
async def get_or_create(
    user_create_body: UserCreateBody,
    user: dict = Depends(validate_dependency),
    session: AsyncSession = Depends(database.get_async_session),
):
    id = user.get("id")
    inviteCode = user_create_body.inviteCode
    isPremium = user_create_body.isPremium
    need_to_see_daily_check_in = False

    db_user = await session.get(User, id)
    if db_user:
        reward = await session.get(Reward, db_user.id)
        if not already_claimed_today(reward.lastReward):
            if check_streak(reward.lastReward):
                reward.day = 1
            else:
                reward.day += 1

            need_to_see_daily_check_in = True
            reward.lastReward = datetime.now()
            if reward.day >= 8:
                reward.day = 1
            await session.commit()

        if db_user.lastLogin is None:
            db_user.lastLogin = datetime.now()
            await session.commit()
            daily_activity = await activity.get_or_create_daily_activity(session)
            await activity.update_daily_activity_users_entered(session, daily_activity)
        elif db_user.lastLogin.day != datetime.now().day:
            daily_activity = await activity.get_or_create_daily_activity(session)
            await activity.update_daily_activity_users_entered(session, daily_activity)

        db_user.lastLogin = datetime.now()
        await session.commit()

        return {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "day": reward.day,
            "need_to_see_daily_check_in": need_to_see_daily_check_in,
            "heSeeWelcomeScreen": True,
        }

    user_create = UserCreate(
        id=id,
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        username=user.get("username"),
    )
    new_user, new_reward = await user_crud.create_user(
        user_create, inviteCode, isPremium, session
    )
    new_reward.lastReward = datetime.now()
    new_user.lastLogin = datetime.now()
    await session.commit()

    age = user_crud.calculate_age(new_user.id)
    coins = user_crud.calculate_new_account_reward(age, isPremium)
    title, percent = user_crud.calculate_account_age_name(age)

    await user_crud.update_wallet(session, new_user.id, coins)

    return {
        "id": new_user.id,
        "first_name": new_user.first_name,
        "day": new_reward.day,
        "need_to_see_daily_check_in": True,
        "heSeeWelcomeScreen": False,
        "age": age,
        "age_coins": coins,
        "title": title,
        "percent": percent,
    }


@router.get("/me")
async def get_me(
    session: AsyncSession = Depends(database.get_async_session),
    user_data=Depends(validate_dependency),
):
    user = await user_crud.get_user(user_data.get("id"), session)
    reward = await session.get(Reward, user_data.get("id"))

    if reward.day >= 8:
        reward.day = 1
        await session.commit()

    farm = user.wallet.farm
    time_passed = None
    need_to_claim = False

    current_plus_every_second, next_day_plus = get_plus_every_second_for_day(reward.day)
    current_farm_reward = None
    total_duration = settings.farm_seconds
    if farm:
        time_passed = datetime.now() - farm.created_at
        if time_passed > timedelta(seconds=total_duration):
            need_to_claim = True
            time_passed = timedelta(seconds=total_duration)
        current_farm_reward = current_plus_every_second * time_passed.seconds
        time_passed = time_passed.seconds

    reffers_checked = user.account.reffers_checked
    rewards_list = task.get_rewards()

    rewards_response = []

    for count, reward in rewards_list.items():
        claimed = False
        if reffers_checked:
            if count <= reffers_checked:
                claimed = True
        rewards_response.append({"reward": reward, "claimed": claimed, "count": count})

    user.updated_at = datetime.now()
    await session.merge(user)
    await session.commit()

    db_wallet = await wallet.get_wallet_by_id(session, user.id)

    return {
        "id": user.id,
        "last_name": user.last_name,
        "first_name": user.first_name,
        "username": user.username,
        "account": user.account,
        "wallet": user.wallet,
        "time_passed": time_passed,
        "need_to_claim": need_to_claim,
        "current_farm_reward": current_farm_reward,
        "plus_every_second": current_plus_every_second,
        "next_day_plus_every_second": next_day_plus,
        "total_duration": total_duration,
        "reffer_rewards": rewards_response,
        "current_level": db_wallet.level,
        "total_volume": db_wallet.total_volume,
        "volume_levels": wallet.VOLUME_LEVELS
    }


@router.post("/save_wallet_address")
async def save_wallet_address(
    save_wallet: SaveWallet,
    session: AsyncSession = Depends(database.get_async_session),
    user=Depends(validate_dependency),
):
    wallet = await session.get(Wallet, user.get("id"))
    if wallet:
        wallet.wallet_address = save_wallet.address
        wallet.wallet_type = save_wallet.name
        await session.commit()

        daily_activity = await activity.get_or_create_daily_activity(session)
        await activity.update_daily_activity_connected_wallets(session, daily_activity)


@router.get("/daiy_check_in")
async def daily_check_in(
    session: AsyncSession = Depends(database.get_async_session),
    user_data=Depends(validate_dependency),
):
    rewards = get_rewards()
    user_reward = await session.get(Reward, user_data.get("id"))
    current_plus_every_second, _ = get_plus_every_second_for_day(user_reward.day)

    now = datetime.now()
    time_left_for_next_reward = (
        datetime(now.year, now.month, now.day + 1) - datetime.now()
    )
    return {
        "rewards": rewards,
        "current_plus_every_second": current_plus_every_second,
        "time_left_for_next_reward": time_left_for_next_reward.seconds,
    }
