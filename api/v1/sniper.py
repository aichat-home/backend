from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from schemas import SniperNotificate
from utils import validate, sniper
from bot import bot
from db import database


router = APIRouter(tags=["Sniper"])


@router.post("/notificate")
async def notificate_sniper(
    sniper_notificate: SniperNotificate,
    session: AsyncSession = Depends(database.get_async_session),
    validate=Depends(validate.sniper_service_validate),
):
    order = await sniper.get_order_by_id(sniper_notificate.order_id, session)

    confirmed = sniper_notificate.confirmed
    if confirmed:
        confirmation_text = "Sniper went successfully"
    else:
        confirmation_text = "Sniper failed"

    await bot.send_message(
        chat_id=sniper_notificate.user_id,
        text=f"{confirmation_text}\nYou bought {sniper_notificate.token_amount} for {order.sol_amount}",
    )
    await session.delete(order)


@router.get("/orders/{token_address}")
async def active_orders(
    token_address: str,
    session: AsyncSession = Depends(database.get_async_session),
    validate=Depends(validate.sniper_service_validate),
):
    orders = await sniper.get_orders_by_token(token_address, session)

    return orders
