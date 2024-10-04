import asyncio
from utils import notifications

from core import settings


async def send_farm_claim_notification(user_id: int):
    await asyncio.sleep(settings.farm_seconds - 1800)
    await notifications.send_notification(user_id, 'You can claim your reward after 30 minutes')
