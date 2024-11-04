from aiohttp import ClientSession

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import settings
from models import Order, SolanaWallet


async def create_order(session: AsyncSession, **fields):
    order = Order(**fields)
    session.add(order)
    await session.commit()
    return order


async def get_all_orders(wallet_id: int, session: AsyncSession):
    stmt = select(Order).filter(Order.wallet == wallet_id)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    return orders


async def get_order_by_id(order_id: int, session: AsyncSession):
    order = await session.get(Order, order_id)
    return order


async def get_orders_by_token(token_address: str, session: AsyncSession):
    stmt = (
        select(
            Order.sol_amount,
            Order.slippage,
            Order.mev_protection,
            Order.id,
            Order.token_address,
            Order.gas,
            SolanaWallet.wallet,
            SolanaWallet.encrypted_private_key,
        )
        .join(SolanaWallet, SolanaWallet.id == Order.wallet)
        .filter(Order.token_address == token_address)
    )
    result = await session.execute(stmt)
    orders = result.fetchall()

    return [
        {
            "order_id": order.id,
            "token_address": order.token_address,
            "sol_amount": order.sol_amount,
            "slippage": order.slippage,
            "mev_protection": order.mev_protection,
            "gas": order.gas,
            "user_id": order.wallet,
            "private_key": order.encrypted_private_key.decode(),
        }
        for order in orders
    ]


async def remove_order(order_id: int, session: AsyncSession):
    order = await session.get(Order, order_id)
    await session.delete(order)
    await session.commit()


async def create_order_service(
    user_id, order: Order, private_key: bytes, session: ClientSession
):
    data = {
        "user_id": user_id,
        "order_id": order.id,
        "token_address": order.token_address,
        "slippage": order.slippage,
        "mev_protection": order.mev_protection,
        "gas": order.gas,
        "private_key": private_key.decode(),
        "sol_amount": order.sol_amount,
    }
    headers = {"x-access-token": settings.sniper_access_token}
    async with session.post(
        "http://sniper:9000/snipe", json=data, headers=headers
    ) as response:
        response = await response.json()


async def update_order_service(
    user_id, order: Order, private_key: bytes, session: ClientSession
):
    data = {
        "user_id": user_id,
        "order_id": order.id,
        "token_address": order.token_address,
        "slippage": order.slippage,
        "mev_protection": order.mev_protection,
        "gas": order.gas,
        "private_key": private_key.decode(),
        "sol_amount": order.sol_amount,
    }
    headers = {"x-access-token": settings.sniper_access_token}
    async with session.patch(
        f"http://sniper:9000/snipe/{order.id}", json=data, headers=headers
    ) as response:
        response = await response.json()


async def remove_order_service(order_id: int, session: ClientSession):
    headers = {"x-access-token": settings.sniper_access_token}
    async with session.delete(
        f"http://sniper:9000/snipe/{order_id}", headers=headers
    ) as response:
        response = await response.json()
