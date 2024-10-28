from fastapi import APIRouter

from sqlalchemy.ext.asyncio import AsyncSession

from schemas import SniperNotificate
from utils import validate, sniper
from bot import bot


router = APIRouter(tags=['Sniper'])


@router.post('/notificate', dependencies=[validate.sniper_service_validate])
async def notificate_sniper(session: AsyncSession, sniper_notificate: SniperNotificate):
    order = await sniper.get_order_by_id(sniper_notificate.order_id, session)

    confirmed = sniper_notificate.confirmed
    if confirmed:
        confirmation_text = 'Sniper went successfully'
    else:
        confirmation_text = 'Sniper failed'

    await bot.send_message(
        chat_id=sniper_notificate.user_id,
        text=f'{confirmation_text}\nYou bought {sniper_notificate.token_amount} for {order.sol_amount}'
    )
    await session.delete(order)
