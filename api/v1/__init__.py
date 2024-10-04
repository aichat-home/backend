from fastapi import APIRouter

from .adds import router as add_router
from .user import router as user_router
from .leaderboard import router as leaderboard_router
from .refrerals import router as refferals_router
from .task import router as task_router
from .farm import router as farm_router
from .partners import router as partners_router


api_router = APIRouter()
partners_api_router = APIRouter()

api_router.include_router(add_router, prefix='/add')
api_router.include_router(user_router, prefix='/users')
api_router.include_router(leaderboard_router, prefix='/leaderboard')
api_router.include_router(refferals_router, prefix='/referrals')
api_router.include_router(task_router, prefix='/task')
api_router.include_router(farm_router, prefix='/farm')
partners_api_router.include_router(partners_router, prefix='/partners', dependencies=[])
