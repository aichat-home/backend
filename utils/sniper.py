from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import Order



async def create_order(
        session: AsyncSession,
        **fields
    ):
    order = Order(
        **fields
    )
    session.add(order)
    await session.commit()


async def get_all_orders(wallet_id: int, session: AsyncSession):
    stmt = select(Order).filter(Order.wallet == wallet_id)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    return orders


async def update_order(order_id: int, session: AsyncSession, **fields):
    order = await session.get(Order, order_id)
    for key, value in fields.items():
        setattr(order, key, value)
    await session.commit()


async def remove_order(order_id: int, session: AsyncSession):
    order = await session.get(Order, order_id)
    del order
    await session.commit()