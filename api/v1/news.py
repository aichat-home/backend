from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


from utils import news
from models import New
from db import database
from schemas import NewsResponse



router = APIRouter(tags=['News'])


@router.get('', response_model=list[NewsResponse])
async def get_news(session: AsyncSession = Depends(database.get_async_session)):
    """
    Returns the latest news from CoinTelegraph.
    """
    stmt = select(New)
    result = await session.execute(stmt)
    news_list = result.scalars().all()

    if len(news_list) > 0:
        new = news_list[0]
        created_at = new.created_at
        now = datetime.now()

        if now - created_at < timedelta(days=1):
            return news_list

    for new in news_list:
        await session.delete(new)

    news_list = news.fetch_cointelegraph_news()
    for new in news_list:
        new = New(
            title=new['title'] ,
            description=new['description'],
            creator_name=new['creator_name'],
            image_url=new['image_url'],
            link=new['link'] 
            )
        session.add(new)
    await session.commit()

    return news_list
