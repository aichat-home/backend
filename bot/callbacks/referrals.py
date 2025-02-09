from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select

from bot.texts import texts
from bot.keyboards import to_home
from models import Account, RefferAccount
from utils import wallet


router = Router()


@router.callback_query(F.data == 'referral')
async def refresh(callback_query: CallbackQuery, session: AsyncSession):
    account = await session.get(Account, callback_query.from_user.id)
    result = await session.execute(
        select(RefferAccount)
        .join(RefferAccount.user)  # Join RefferAccount with its related User
        .filter(RefferAccount.oneWhoInvited == callback_query.from_user.id)  # Filtering by the ID of the one who invited
        .options(joinedload(RefferAccount.user))  # Eager loading the user relationship
    )

    # Fetch all referred accounts
    referrals = result.scalars().all()

    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)

    await callback_query.message.edit_caption(caption=texts.REFERRALS_TEXT.format(
        referral_code=account.inviteCode,
        referral_count=len(referrals),
        sol_earned=db_wallet.commision_earned
        ), reply_markup=to_home())

    await callback_query.answer()
