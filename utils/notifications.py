from bot import bot, media


async def send_notification(user_id, notification_text):
    await bot.send_animation(user_id, media, caption=notification_text)