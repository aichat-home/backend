from bot import bot


async def send_notification(user_id, notification_text):
    await bot.send_message(user_id, notification_text)