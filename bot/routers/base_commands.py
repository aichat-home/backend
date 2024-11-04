from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import start_keyboard
from bot.texts import texts
from bot.image import start_photo
from models import User, Settings, RefferAccount
from utils import wallet, user as user_crud
from schemas import UserCreate



router = Router()



@router.message(CommandStart())
async def start(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user = await session.get(User, message.from_user.id)
    settings = None
    if not user:
        user, _ = await user_crud.create_user(
            UserCreate(
                id = message.from_user.id,
                username = message.from_user.username,
                first_name = message.from_user.first_name,
                last_name = message.from_user.last_name,
            ),
            inviteCode=None,
            isPremium=message.from_user.is_premium,
            session=session,
        )
        session.add(user)
        await session.commit()

        settings = Settings(id=user.id)
        session.add(settings)
        await session.commit()
    if settings is None:
        settings = await session.get(Settings, user.id)
        if settings is None:
            settings = Settings(id=user.id)
            session.add(settings)
            await session.commit()

    db_wallet = await wallet.get_wallet_by_id(session, message.from_user.id)

    if not db_wallet:
        db_wallet = await wallet.create_wallet(session, message.from_user.id)

    balance = await wallet.get_wallet_balance(db_wallet.public_key)
    number = db_wallet.entries if db_wallet.entries is not None else 0
    await message.answer_photo(start_photo, caption=texts.START_TEXT.format(balance=balance, wallet_address=db_wallet.public_key, number=number), reply_markup=start_keyboard)

