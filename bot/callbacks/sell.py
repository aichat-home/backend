from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import sell_keyboard, sell_token as sell_token_keyboard, to_home, swap_confirmation
from bot.states import sell
from utils import wallet, market, image
from session import get_session
from models import Settings
from utils.swap import swap, utils, constants



router = Router()


@router.callback_query(lambda c: c.data == 'sell')
async def sell_token(callback_query: CallbackQuery, session: AsyncSession):
    client_session = get_session()
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)

    tokens = await wallet.get_tokens(db_wallet.public_key)
    mints = await market.get_mints(client_session)

    response_token = []
    for token in tokens.value:
        data = token.account.data.parsed['info']
        mint = data.get('mint')
        amount = data.get('tokenAmount', {}).get('uiAmount', 0)
        data = market.get_token_symbol(mint, mints)
        symbol = data.get('symbol')

        # if amount:
        response_token.append((mint, amount, symbol))

    await callback_query.message.edit_caption(caption='Your tokens: ', reply_markup=sell_keyboard(response_token))
    await callback_query.answer()
    await session.commit()


@router.callback_query(F.data.startswith('show_sell_'))
async def show_token(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = callback_query.data.split('_')
    mint = data[2]
    

    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    token = await wallet.get_token(db_wallet.public_key, mint)
    amount = 0

    if token:
        amount = token.value[0].account.data.parsed['info'].get('tokenAmount', {}).get('uiAmount', 0)
        await callback_query.answer()

    client_session = get_session()
    token_data = await market.get_token_data_by_address(client_session, mint)
    await state.update_data(token_data=token_data)
    pnl, average_buy_price = await wallet.get_average_buy_price_and_pnl(db_wallet.id, mint, session)
    pnl = f'{pnl:.2f}%' if pnl != 0 else 'N/A'

    profit_can_made = 'N/A'
    sell_price = None

    if average_buy_price:
        pair_address, program_id = await utils.get_pair_address(mint, client_session)

        if program_id == constants.RAY_V4:
            pool_keys = await utils.fetch_pool_keys(pair_address)
        elif program_id == constants.RAY_CP:
            pool_keys = await utils.fetch_pool_keys_cp(pair_address)
        token_price, token_decimals = await utils.get_token_price(pool_keys)
        sell_price = token_price * constants.SOL_DECIMAL / (10 ** token_decimals)

        profit_can_made = f'{(sell_price / average_buy_price) * 100 - 100:.2f}%'


    if token_data:
        text = (
            f'Sell <a href="https://solscan.io/token/{mint}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
            f'💳 My Balance: <code>{amount} {token_data["symbol"].upper()}</code> (${token_data["price"] * amount:.2f})\n\n'

            f'💸  Price: {token_data["price"]}\n'
            f'💵  MCap: ${market.format_number(token_data["market_cap"])}\n'
            f'🔎  24h: {token_data["h24"]:.4f}%\n'
            f'💰  Liquidity: ${market.format_number(token_data["liquidity"])}\n\n'

            f'Statistics: \n\n'

            f'PNL: {pnl}\n'
            f'Profit Can Made: {profit_can_made}'
        )
        reply_markup = sell_token_keyboard(mint)

        image_buffer = image.create_image(
                symbol=f"{token_data['symbol']}",
                price=f"${token_data['price']}",
                market_cap=f"${market.format_number(token_data['market_cap'])}",
                change=f"{token_data['h24']:.3f}%",
                liquidity=f"${market.format_number(token_data['liquidity'])}",
                background_path='bg.png'
            )

        banner = BufferedInputFile(image_buffer.getvalue(), filename="price_image.png")

        photo = InputMediaPhoto(media=banner, caption=text)
    else:
        text = 'Token not found'
        reply_markup = None

    try:
        await callback_query.message.edit_media(
            media=photo,
            reply_markup=reply_markup
        )
        await callback_query.answer()
    except Exception:
        pass

    await callback_query.answer()


@router.callback_query(F.data.startswith('sell_'))
async def sell_token_amount(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = callback_query.data.split('_')
    mint = data[1]
    amount = data[2]

    data = await state.get_data()
    token_data = data.get('token_data')
    print(data, token_data)


    if amount == 'x':
        await state.set_state(sell.SellState.percent)
        await callback_query.message.edit_caption(caption=
            'Enter percent',
            reply_markup=to_home()
        )
        await callback_query.answer()
        return
    
    elif amount == 'amount':
        await state.set_state(sell.SellState.amount)
        await callback_query.message.edit_caption(caption=
            'Enter amount',
            reply_markup=to_home()
        )
        await callback_query.answer()
        return
    else:
        percent = float(amount)

        db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
        
        
        settings = await session.get(Settings, callback_query.from_user.id)
        
        token = await wallet.get_token(db_wallet.public_key, mint)
        mint, balance, decimals = wallet.parse_token_mint_address_amount_decimals(token.value[0])
        amount = balance * (percent / 100)

        if settings.extra_confirmation:
            
            await state.set_state(sell.SellState.confirmation)
            await callback_query.message.edit_caption(caption=
                f'You are about to sell {amount} {token_data["symbol"].upper()} for SOL. Please confirm.',
                reply_markup=swap_confirmation()
            )
            return
        

        data = await state.get_data()
        await swap.sell_token(
            token_data=token_data,
            db_wallet=db_wallet,
            slippage=settings.sell_slippage,
            amount=amount,
            message_or_callback=callback_query,
            session=session,
        )


