import base64

from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import Partner




class CreatePartnerState(StatesGroup):
    waiting_for_name = State()


async def create_partner(message: Message, session: AsyncSession):
    stmt = select(Partner.id).order_by(Partner.id.desc())
    last_id = await session.execute(stmt)
    last_id = last_id.scalars().first()
    partner_name = message.text
    invite_code = base64.b64encode(str(partner_name).encode('ascii')).decode('ascii')
    partner = Partner(id=last_id + 1, name=partner_name, inviteCode=invite_code)
    session.add(partner)
    await session.commit()
    await message.answer(f'Partner {partner_name} created with invite code https://t.me/BeamTapBot/Dapp?startapp={invite_code}')  