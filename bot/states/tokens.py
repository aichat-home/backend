from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.enums.parse_mode import ParseMode

from sqlalchemy.ext.asyncio import AsyncSession

from session import get_session
from utils import market, wallet, image
from bot.keyboards import buy_keyboard
from bot.image import start_photo



class TokenState(StatesGroup):
    token = State()


async def handle_token(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    reply_markup = None
    if current_state == TokenState.token.state:
        text = message.text
        if text.startswith('https://'):
            text = text.replace('https://', '')
            if text.startswith('birdeye'):
                token = text.split('/')[2].split('?')[0]
            else:
                await message.answer('You can insert url only from Birdeye', reply_markup=reply_markup)
                await state.clear()
        else:
            token = message.text
        
        client_session = get_session()
        token_data = await market.get_token_data_by_address(client_session, token)
        if token_data:
            db_wallet = await wallet.get_wallet_by_id(session, message.from_user.id)
            balance = await wallet.get_wallet_balance(db_wallet.public_key)
            text = (
            f'Buy <a href="https://solscan.io/token/{token}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
            f'💳 My Balance: <code>{balance} SOL</code>\n\n'

            f'💸  Price: {token_data["price"]}\n'
            f'💵  MCap: ${market.format_number(token_data["market_cap"])}\n'
            f'🔎  24h: {token_data["h24"]:.4f}%\n'
            f'💰  Liqudity: ${market.format_number(token_data["liquidity"])}\n'
        )
            reply_markup = buy_keyboard(token)
            await state.update_data(token_data=token_data)

            image_buffer = image.create_image(
                symbol=f"{token_data['symbol']}",
                price=f"${token_data['price']}",
                market_cap=f"${market.format_number(token_data['market_cap'])}",
                change=f"{token_data['h24']:.3f}%",
                liquidity=f"${market.format_number(token_data['liquidity'])}",
                background_path='bg.png'
            )

            banner = BufferedInputFile(image_buffer.getvalue(), filename="price_image.png")

        else:
            text = "Token not found."
            banner = start_photo
        await message.answer_photo(photo=banner, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        await state.clear()