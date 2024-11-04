from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from core import settings
from db import database
from bot.middlewares import DbSessionMiddleware


bot = Bot(settings.telegram_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

<<<<<<< HEAD
=======
ADMIN_IDS = (540314239, 1795945549)

photo = FSInputFile('bot/media/start.png')
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
    text = ("BeamBot's unique value stems from its seemless and revolutionary one-click trading experience and market-leading artifical intelligence agents.\n\n"
            
            "It boasts an ultra-simplified UI, set within a custom-built Mini-App and platform, along with AI agents capable of offering users enhanced trading security, asset analysis and market tracking prior to placing an order. These agents are able to trade assets by themselves, autonomously, whilst users passively reap the rewards. What's more, Beambot offers a dedicated platform that enables agents to be uploaded and speculated on by community members the same way a token is, valued by their utility and popularity. \n\n"

            "As a result, BeamBot provides an innovative and superior option to the complex, slow alternatives that fail to efficiently integrate within Telegram's high-potential platform."
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

        users_sent = 0
        for user in users:
            tasks.append(send_message_to_user(user.id, message.text))

            if len(tasks) == 25:
                await asyncio.gather(*tasks)
                tasks = []
                users_sent += 25
                if users_sent % 1000 == 0:
                    await bot.send_message(message.from_user.id, f'Sent {users_sent} users')
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
    except Exception as e:
        print(f'Error sending message to {user_id}: {e}')


>>>>>>> dev
dp.update.middleware(DbSessionMiddleware(database))