from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from bot.texts import texts
from bot.keyboards import to_home
from bot.image import giveaway_photo
from core import settings


router = Router()


text = ('We’re offering community members the opportunity to take part in our <b>$5000 giveaway!</b>\n\n'

            'The rules are simple…\n\n'

            'You’ll earn an <b>increased amount</b> of entries depending on how much you trade, maximising your <b>overall chance</b> of winning the $5000 prize.\n\n'

            '<b>1 Entry</b> = per trade between $5 and $20\n\n'

            '<b>4 Entries</b> = per trade between $20 and $100\n\n'

            '<b>10 Entries</b> = per trade between $100 and $1000\n\n'

            '<b>200 Entries</b> = per trade over $1000+ \n\n'

            '<i>Winner announced in channel and on socials! 🔥</i>'
    )


photo = InputMediaPhoto(media=giveaway_photo, caption=text)


@router.callback_query(F.data == 'giveaway')
async def giveaway(callback_query: CallbackQuery):
    
    await callback_query.message.edit_media(media=photo, reply_markup=to_home())

    await callback_query.answer()
