from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.enums.chat_member_status import ChatMemberStatus


from db import database
from models import User
from bot import bot
from core import settings


router = APIRouter(tags=['Parners'])



@router.post('/game/check')
async def game_check(inviteCode: str, userId: int, session: AsyncSession = Depends(database.get_async_session)):
    """
    Check if user is from a partner and has entered the game with the given invite code.
    return status: entered if user is from a partner and has entered the game with the given invite code
    return status: not from partner if user is not from a partner
    return status: user not found if user not found in the database
    """
    user = await session.get(User, userId)
    if user:
        if user.partner == inviteCode:
            return {'status': 'entered'}
        return {'status': 'not from partner'}
    return {'status': 'user not found'}
    

@router.post('/channel/check')
async def channel_check(userId: int):
    """
    Check if user is in the channel.
    return status: ok if user is in the channel
    return status: not in channel if user is not in the channel
    """
    chat_member = await bot.get_chat_member(settings.telegram_channel_id, userId)

    if chat_member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        return {'status': 'ok'}
    return {'status': 'not in channel'}
