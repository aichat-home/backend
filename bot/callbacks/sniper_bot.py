from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import sniper_show_keyboar, sniper_token, cancel_sniper_config, show_all_snipers, edit_sniper_token, to_home
from bot.states import sniper as sniper_state
from session import get_session
from utils import sniper, wallet, market
from models import Order


router = Router()


@router.callback_query(F.data == 'sniper_bot')
async def get_new_tokens(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    orders = await sniper.get_all_orders(db_wallet.id, session)
    await state.set_state(sniper_state.SnipeState.token)
    await callback_query.message.edit_caption(caption=(f'Active Snipers: {len(orders)}\n\n'

                                'Paste token address to create new sniper!'
                                ),
                                reply_markup=sniper_show_keyboar()
                                )


@router.callback_query(F.data == 'sniper_list')
async def sniper_list(callback_query: CallbackQuery, session: AsyncSession):
    db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
    orders = await sniper.get_all_orders(db_wallet.id, session)
    
    await callback_query.message.edit_caption(caption='Active snipers:', reply_markup=show_all_snipers(orders))


@router.callback_query(F.data.startswith('snipe_'))
async def refresh_snipe(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        data = await state.get_data()
        client_session = get_session()
        token = callback_query.data.split('_')[1]
        token_data = await market.get_token_data_by_address(client_session, token)
        if token_data:
            db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
            balance = await wallet.get_wallet_balance(db_wallet.public_key)
            await state.update_data(token_data=token_data, db_wallet=db_wallet, balance=balance)

            text = (
                    f'Buy <a href="https://solscan.io/token/{token}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                    f'💳 My Balance: <code>{balance} SOL</code>\n\n'

                    f'💸  Price: {token_data["price"]}\n'
                    f'💵  MCap: ${market.format_number(token_data["market_cap"])}\n'
                    f'🔎  24h: {token_data["h24"]:.4f}%\n'
                    f'💰  Liqudity: ${market.format_number(token_data["liquidity"])}\n'
                )
            slippage = data.get('slippage', 15)
            gas = data.get('gas', 0.001)
            amount = data.get('amount', 0.1)
            mev = data.get('mev', True)
            await callback_query.message.edit_caption(caption=text, reply_markup=sniper_token(slippage, gas, amount, token, mev))
    except Exception as e:
        print(e)
        await callback_query.answer()


@router.callback_query(F.data == 'sniper_slippage')
async def change_sniper_slippage(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.SnipeState.slippage)
    await callback_query.message.edit_caption(caption='Enter slippage', reply_markup=cancel_sniper_config(token_data.get('address')))


@router.callback_query(F.data == 'sniper_amount')
async def change_sniper_amount(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.SnipeState.amount)
    await callback_query.message.edit_caption(caption='Enter amount', reply_markup=cancel_sniper_config(token_data.get('address')))



@router.callback_query(F.data == 'sniper_gas')
async def change_sniper_gas(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.SnipeState.gas)
    await callback_query.message.edit_caption(caption='Enter gas', reply_markup=cancel_sniper_config(token_data.get('address')))


@router.callback_query(F.data == 'sniper_mev')
async def change_sniper_gas(callback_query: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        token_data = data.get('token_data')
        slippage = data.get('slippage', 15)
        gas = data.get('gas', 0.001)
        amount = data.get('amount', 0.1)
        mev = not data.get('mev', True)
        await state.update_data(mev=mev)
        await callback_query.message.edit_reply_markup(reply_markup=sniper_token(slippage, gas, amount, token_data['address'], mev))
    except Exception as e:
        print(e)
        await callback_query.answer()


@router.callback_query(F.data == 'create_sniper')
async def create_sniper(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    db_wallet = data.get('db_wallet')

    amount = data.get('amount', 0.1)
    slippage = data.get('slippage', 15)
    gas = data.get('gas', 0.001)
    token_data = data.get('token_data')
    mev = data.get('mev', True)

    order = await sniper.create_order(
            session=session, 
            sol_amount=amount, 
            slippage=slippage, 
            gas=gas, 
            token_address=token_data.get('address'), 
            mev_protection=mev, 
            wallet=db_wallet.id
        )
    db_wallet.number_of_snipes += 1
    session.add(db_wallet)
    await session.commit()
    
    
    
    client_session = get_session()
    await sniper.create_order_service(callback_query.from_user.id, order, db_wallet.encrypted_private_key, client_session)
    
    await callback_query.message.edit_caption(caption='Sniper created successfully', reply_markup=sniper_show_keyboar())
    


@router.callback_query(F.data.startswith('edit_sniper_show'))
async def edit_sniper(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    order_id = callback_query.data.split('_')[3]
    order = await sniper.get_order_by_id(int(order_id), session)
    await state.update_data(order=order)

    client_session = get_session()
    data = await state.get_data()
    token_data = await market.get_token_data_by_address(client_session, order.token_address)
    if token_data:
        await state.update_data(token_data=token_data)
        db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
        balance = await wallet.get_wallet_balance(db_wallet.public_key)

    text = (
                f'Buy <a href="https://solscan.io/token/{order.token_address}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                f'💳 My Balance: <code>{balance} SOL</code>\n\n'

                f'💸  Price: {token_data["price"]}\n'
                f'💵  MCap: ${market.format_number(token_data["market_cap"])}\n'
                f'🔎  24h: {token_data["h24"]:.4f}%\n'
                f'💰  Liqudity: ${market.format_number(token_data["liquidity"])}\n'
            )
    await callback_query.message.edit_caption(caption=text, reply_markup=edit_sniper_token(order.slippage, order.gas, order.sol_amount, order.mev_protection, order.id))



@router.callback_query(F.data == 'edit_sniper_slippage')
async def change_sniper_slippage(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.EditSniperState.slippage)
    await callback_query.message.edit_caption(caption='Enter slippage', reply_markup=cancel_sniper_config(token_data.get('address')))


@router.callback_query(F.data == 'edit_sniper_amount')
async def change_sniper_amount(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.EditSniperState.amount)
    await callback_query.message.edit_caption(caption='Enter amount', reply_markup=cancel_sniper_config(token_data.get('address')))



@router.callback_query(F.data == 'edit_sniper_gas')
async def change_sniper_gas(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_data = data.get('token_data')
    await state.set_state(sniper_state.EditSniperState.gas)
    await callback_query.message.edit_caption(caption='Enter gas', reply_markup=cancel_sniper_config(token_data.get('address')))


@router.callback_query(F.data == 'edit_sniper_mev')
async def change_sniper_gas(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        token_data = data.get('token_data')
        order: Order = data.get('order')
        order.mev_protection = not order.mev_protection
        session.add(order)
        await session.commit()
        if token_data:
            await state.update_data(token_data=token_data)
            db_wallet = await wallet.get_wallet_by_id(session, callback_query.from_user.id)
            balance = await wallet.get_wallet_balance(db_wallet.public_key)
            client_session = get_session()
            await sniper.update_order_service(callback_query.from_user.id, order, db_wallet.encrypted_private_key, client_session)

        text = (
                    f'Buy <a href="https://solscan.io/token/{order.token_address}">🅴</a> <b>{token_data["symbol"].upper()}</b>\n'
                    f'💳 My Balance: <code>{balance} SOL</code>\n\n'

                    f'💸  Price: {token_data["price"]}\n'
                    f'💵  MCap: ${market.format_number(token_data["market_cap"])}\n'
                    f'🔎  24h: {token_data["h24"]:.4f}%\n'
                    f'💰  Liqudity: ${market.format_number(token_data["liquidity"])}\n'
                )
        await callback_query.message.edit_caption(caption=text, reply_markup=edit_sniper_token(order.slippage, order.gas, order.sol_amount, order.mev_protection, order.id))
    except Exception as e:
        print(e)
        await callback_query.answer()


@router.callback_query(F.data.startswith('delete_sniper_'))
async def delete_sniper(callback_query: CallbackQuery, session: AsyncSession):
    order_id = int(callback_query.data.split('_')[2])
    await sniper.remove_order(order_id, session)

    await callback_query.message.edit_caption(caption='Sniper removed successfully', reply_markup=to_home())
    session = get_session()
    await sniper.remove_order_service(order_id, session)