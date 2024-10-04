from fastapi import APIRouter
from .v1 import api_router as v1_router, partners_api_router


router = APIRouter()

router.include_router(v1_router, prefix='/v1')
