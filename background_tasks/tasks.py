import asyncio
from utils import notifications

from core import settings


async def send_farm_claim_notification(user_id: int):
    await asyncio.sleep(settings.farm_reward)
    await notifications.send_notification(user_id, 'Your bags are full! 💰 Harvest your farming rewards and climb the leaderboard 😍🔥')
