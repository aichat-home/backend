import base64

from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder



def inline_builder(webapp_url: str, user_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    invite_code = base64.b64encode(str(user_id).encode('ascii')).decode('ascii')


    builder.row(InlineKeyboardButton(
                    text='🕹️ PLay',
                    web_app=WebAppInfo(url=webapp_url)
                    )
                )
    builder.row(InlineKeyboardButton(
                    text='😎 Invite Friends',
                    url=f'https://t.me/share/url?url=https://t.me/webapptesst_bot/Dapp?startapp={invite_code}&text=Hey! Join this amazing app and earn rewards together!'
                    ),
                    InlineKeyboardButton(
                    text='🤠 Join Community',
                    url='https://t.me/BeambotXYZ'
                    )
                )
    builder.row(InlineKeyboardButton(
                    text='🐦 Twitter',
                    url='https://x.com/BeamBotXYZ'
                    )
                )
    
    return builder.as_markup()


