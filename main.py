from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import Base, database
from api import router, partners_api_router
from utils import validate_dependency
from core import settings
from admin import create_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        pass


app = FastAPI(lifespan=lifespan)

app.include_router(router=router, prefix='/api', dependencies=[Depends(validate_dependency)])
app.include_router(router=partners_api_router, prefix='/api')
app.mount('/static', StaticFiles(directory='static'), name='static')
admin = create_admin(app)


origins = [
    settings.webapp_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)