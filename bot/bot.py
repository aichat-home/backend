import asyncio

import base64
from typing import Callable, Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile, TelegramObject
from aiogram.filters import CommandStart, Command
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import settings
from .inline import inline_builder
from db import database
from models import User, Partner


bot = Bot(settings.telegram_token)
dp = Dispatcher()

ADMIN_IDS = (540314239, 1795945549)

photo = FSInputFile('bot/media/start.jpg')
notification_photo = FSInputFile('bot/media/notification.jpg')


class NotifyState(StatesGroup):
    waiting_for_message = State()


class CreatePartnerState(StatesGroup):
    waiting_for_name = State()


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db  # Your database service that has `get_async_session`

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Any],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        # Generate a session using the async session generator
        async for session in self.db.get_async_session():
            # Inject session into data (so handlers can access it)
            data['session'] = session

            # Proceed with the handler
            return await handler(event, data)



@dp.message(CommandStart())
async def start(message: Message):
    text = ('👽 Welcome to the world of BeamBot 🚀\n\n'
            'Calling all humanoids, the depths of space are yours to fight for, set to the tune of cryptocurrency and special missions... 🌒\n'
            'As an ambitious galactic explorer, you find yourself on the verge of riches and wealth, where collecting crystals and coins will line your pockets with the most expensive space dust... 🌌'
            )
    
    
    await bot.send_photo(message.chat.id, photo=photo, caption=text, reply_markup=inline_builder(settings.webapp_url, message.chat.id))


@dp.message(Command('create_partner'))
async def create_partner(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await state.set_state(CreatePartnerState.waiting_for_name)
        await message.answer('Send name of partner')


@dp.message(Command('notify'))
async def notify(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await state.set_state(NotifyState.waiting_for_message)
        await message.answer('Send message')


@dp.message()
async def waiting_for_message(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state == NotifyState.waiting_for_message.state:
        result = await session.execute(select(User))
        users = result.scalars().all()
        tasks = []

        await bot.send_message(message.from_user.id, 'Starting')

        for user in users:
            tasks.append(send_message_to_user(user.id, message.text))

            if len(tasks) == 25:
                await asyncio.gather(*tasks)
                tasks = []
                await asyncio.sleep(1)

    elif current_state == CreatePartnerState.waiting_for_name:
        stmt = select(Partner.id).order_by(Partner.id.desc())
        last_id = await session.execute(stmt)
        last_id = last_id.scalars().first()
        partner_name = message.text
        invite_code = base64.b64encode(str(partner_name).encode('ascii')).decode('ascii')
        partner = Partner(id=last_id + 1, name=partner_name, inviteCode=invite_code)
        session.add(partner)
        await session.commit()
        await message.answer(f'Partner {partner_name} created with invite code https://t.me/BeamTapBot/Dapp?startapp={invite_code}')  
    
    
    
    # Run all tasks concurrently using asyncio.gather
    await asyncio.gather(*tasks)

    await state.clear()

    # Notify admin that the message was broadcasted
    await message.answer(f'Notification sent to {len(users)} users.')


async def send_message_to_user(user_id, text):
    try:
        await bot.send_photo(user_id, notification_photo, caption=text)
    except TelegramBadRequest as e:
        print(f'Error sending message to {user_id}: {e}')


dp.update.middleware(DbSessionMiddleware(database))