from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    async_sessionmaker
)

from core import settings



class Database:

    def __init__(self, url: str, echo: bool) -> None:
        self.engine = create_async_engine(
            url=url,
            echo=echo
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def get_async_session(self):
        async with self.session_factory() as session:
            yield session
            await session.close()


database = Database(
    url=settings.db_url, 
    echo=settings.db_echo
)