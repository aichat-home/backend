import base64
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import selectinload, aliased, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import (
    User, 
    Partner, 
    Account, 
    Wallet, 
    RefferAccount,
    Reward, 
    Farm
    )

from schemas import UserCreate




async def update_wallet(session: AsyncSession, user_id: int, coins: int):
    refferAccount = await session.get(RefferAccount, user_id)
    if refferAccount:
        oneWhoInvitedWallet = await session.get(Wallet, refferAccount.oneWhoInvited)
        if oneWhoInvitedWallet:
            oneWhoInvitedWallet.coins += coins * 0.1
            session.add(oneWhoInvitedWallet)
            refferAccount.earned_coins += coins * 0.1
    
    wallet = await session.get(Wallet, user_id)
    if wallet:
        wallet.coins += coins
        session.add(wallet)
    
    await session.commit()
    return wallet


async def get_user(id: int, session: AsyncSession):
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.account).selectinload(Account.reffers).selectinload(RefferAccount.user),
            selectinload(User.account).selectinload(Account.completedTasks),
            selectinload(User.wallet).selectinload(Wallet.reward),
            selectinload(User.wallet).selectinload(Wallet.farm),
            with_loader_criteria(Farm, Farm.status == 'Process')
        )
        .filter(User.id == id)
    )
    user = result.scalars().first()
    if user:
        user.account.heSeeWelcomeScreen = True
    return user


async def create_user(user: UserCreate, inviteCode: str, isPremium: bool, session: AsyncSession):

    partner = None
    oneWhoInvited = None
    refferAccount = None

    if inviteCode:
        stmt = select(Partner).filter(Partner.inviteCode == inviteCode)
        result = await session.execute(stmt)
        partner = result.scalars().first()

        if partner:
            new_user = User(**user.model_dump(exclude_none=True), partner=partner.inviteCode, isPremium=isPremium)
            # partner.users.append(new_user)
            session.add(new_user)
            session.add(partner)
            await session.commit()
        else:
            stmt = select(Account).filter(Account.inviteCode == inviteCode)
            result = await session.execute(stmt)
            oneWhoInvited = result.scalars().first()
            new_user = User(**user.model_dump(exclude_none=True), isPremium=isPremium)

                # oneWhoInvited.reffers.append(new_user)
            refferAccount = RefferAccount(id=user.id, oneWhoInvited=oneWhoInvited.id) if oneWhoInvited else None

            if refferAccount:
                session.add(refferAccount)
            session.add(new_user)
            await session.commit()
    else:
        new_user = User(**user.model_dump(exclude_none=True), isPremium=isPremium)
        session.add(new_user)

    new_invite_code = base64.b64encode(str(user.id).encode('ascii')).decode('ascii')
    new_account = Account(id=user.id, inviteCode=new_invite_code)
    session.add(new_account)
    await session.commit()

    new_wallet = Wallet(id=user.id)
    session.add(new_wallet)
    await session.commit()
    
    new_reward = Reward(id=user.id, day=1, coinsCount=50)
    session.add(new_reward)
    await session.commit()

    return new_user, new_reward


def calculate_new_account_reward(age: int, isPremium: bool = False) -> int:
    reward = 0
    if isPremium:
        reward += 750
    reward += age * 1250
    if age - 4 > 0:
        reward += (age - 4) * 375
    return reward


def calculate_age(telegram_id: int) -> int:
    id_str = str(telegram_id)
    num_digits = len(id_str)
    
    # Get the current date
    current_date = datetime.now()

    # Return the estimated creation date
    if num_digits >= 10:
        if id_str.startswith('17') or id_str.startswith('16') or id_str.startswith('15'):
            creation_date = datetime(2021, 1, 1)
        elif id_str.startswith('14') or id_str.startswith('13') or id_str.startswith('12'):
            creation_date = datetime(2020, 10, 1)
        elif id_str.startswith('11'):
            creation_date = datetime(2020, 4, 1)
        elif id_str.startswith('10'):
            creation_date = datetime(2019, 11, 1)
        else:
            creation_date = datetime(2022, 1, 1)
    elif num_digits == 9:
        if id_str.startswith('9'):
            creation_date = datetime(2019, 7, 1)
        elif id_str.startswith('8'):
            creation_date = datetime(2019, 4, 1)
        elif id_str.startswith('7'):
            creation_date = datetime(2018, 11, 1)
        elif id_str.startswith('6'):
            creation_date = datetime(2018, 7, 1)
        elif id_str.startswith('5'):
            creation_date = datetime(2018, 2, 1)
        elif id_str.startswith('4'):
            creation_date = datetime(2017, 7, 1)
        elif id_str.startswith('3'):
            creation_date = datetime(2016, 12, 1)
        elif id_str.startswith('2'):
            creation_date = datetime(2016, 2, 1)
        elif id_str.startswith('1'):
            creation_date = datetime(2015, 1, 1)
    elif num_digits <= 8:
        creation_date = datetime(2014, 12, 1)

    # Calculate the account age in years
    account_age_years = (current_date - creation_date).days // 365
    return account_age_years


def calculate_account_age_name(age: int) -> tuple[str, int | float]:
    if age > 11:
        age = 11
    elif age <= 0:
        age = 1
    names = {
        1: ('Rising Star!', 90),
        2: ('Crypto Enthusiast!', 75),
        3: ('Blockchain KING!', 50),
        4: ('Blockchain KING!', 25),
        5: ('HODL Hero!', 17),
        6: ('Decentralized Defender!', 13),
        7: ('Crypto Vanguard!', 8),
        8: ('Blockchain Titan!', 5),
        9: ('Crypto Legend!', 3.5),
        10: ("Satoshi's Vanguard!", 2),
        11: ("Satoshi's Vanguard!", 1)
    }
    return names.get(age)


async def get_user_rank(session: AsyncSession, wallet_id: int):
    # Create the subquery to rank users based on coins
    rank_query = select(
        Wallet.id,
        Wallet.coins,
        func.rank().over(order_by=Wallet.coins.desc()).label("rank")
    ).subquery()
    
    # Final query to get the rank of the specific wallet_id
    query = select(rank_query.c.rank).where(rank_query.c.id == wallet_id)

    # Execute the query and fetch the rank asynchronously
    result = await session.execute(query)
    rank = result.scalar()  # Retrieve the scalar result (rank)
    
    return rank


async def get_reffer_account(user_id: int, session: AsyncSession):
    return await session.get(RefferAccount, user_id)
