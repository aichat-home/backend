from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from models import Settings, Order


start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🤖 Join Mini App', url='https://t.me/BeamTapBot/Dapp'),
        ],
        [
            InlineKeyboardButton(text='💳 Wallet', callback_data='wallet'),
            InlineKeyboardButton(text='❓ Help', callback_data='help'),
            InlineKeyboardButton(text='⚙️ Settings', callback_data='settings')
        ],
        [
            InlineKeyboardButton(text='📈 Buy', callback_data='buy'),
            InlineKeyboardButton(text='📉 Sell & Manage', callback_data='sell'),
        ],
        [
            InlineKeyboardButton(text='Refer Friends', callback_data='referral'),
            InlineKeyboardButton(text='Pump.fun', callback_data='pump.fun'),
            InlineKeyboardButton(text='Sniper Bot', callback_data='sniper_bot'),
        ],
        [
            InlineKeyboardButton(text='🔄 Refresh', callback_data='home')
        ]
    ],
    )


cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='❌ Cancel', callback_data='home')
        ]
    ],
    )


def buy_keyboard(token_address, refresh_prefix='token'):
    builder = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text='❌ Cancel', callback_data='home')
    builder.row(cancel_button, width=1)

    explorer_button = InlineKeyboardButton(text='Explorer', url=f'https://solscan.io/account/{token_address}')
    chart_button = InlineKeyboardButton(text='Chart', url=f'https://dexscreener.com/solana/{token_address}?id=viqdmf33')
    builder.row(explorer_button, chart_button, width=2)

    buy_1_sol = InlineKeyboardButton(text='💲 Buy 0.5 SOL', callback_data=f'buy_0.5_{token_address}')
    buy_5_sol = InlineKeyboardButton(text='💸 Buy 1.0 SOL', callback_data=f'buy_1_{token_address}')
    buy_x_sol = InlineKeyboardButton(text='💵 Buy X SOL', callback_data=f'buy_x_{token_address}')
    builder.row(buy_1_sol, buy_5_sol, buy_x_sol, width=3)

    refresh_button = InlineKeyboardButton(text='🔄 Refresh', callback_data=f'{refresh_prefix}_{token_address}')
    builder.row(refresh_button, width=1)

    return builder.as_markup()


def wallet_keyboard(wallet_address):
    builder = InlineKeyboardBuilder()

    solscan_button = InlineKeyboardButton(text='View on Solscan', url=f'https://solscan.io/account/{wallet_address}')
    colse_button = InlineKeyboardButton(text='⬅ Back to Home', callback_data='home')
    builder.row(solscan_button, colse_button, width=2)

    private_key_button = InlineKeyboardButton(text='🔒 Export private key', callback_data=f'export_confirmation_{wallet_address}')
    builder.row(private_key_button, width=1)

    withdraw_all_button = InlineKeyboardButton(text='💸 Withdraw all SOL', callback_data='withdraw_all')
    withdraw_x_button  = InlineKeyboardButton(text='🤑 Withdraw x SOL', callback_data='withdraw_x')
    builder.row(withdraw_all_button, withdraw_x_button, width=2)

    refresh_button = InlineKeyboardButton(text='🔄 Refresh', callback_data='wallet')
    builder.row(refresh_button, width=1)

    return builder.as_markup()


def export_wallet_confirmation(wallet_address):
    builder = InlineKeyboardBuilder()

    confirm_button = InlineKeyboardButton(text='I Will Not Share My Private Key, Confirm', callback_data=f'export_key_{wallet_address}')
    cancel_button  = InlineKeyboardButton(text='❌ Cancel', callback_data='wallet')
    builder.row(confirm_button, cancel_button, width=1)

    return builder.as_markup()


def close_private_key():
    builder = InlineKeyboardBuilder()

    close_button  = InlineKeyboardButton(text='Close', callback_data='wallet')
    builder.row(close_button, width=1)

    return builder.as_markup()


def withdraw_confirmation():
    builder = InlineKeyboardBuilder()

    confirm_button = InlineKeyboardButton(text='Confirm ✅', callback_data=f'confirm')
    builder.row(confirm_button, width=1)

    cancel_button  = InlineKeyboardButton(text='❌ Cancel', callback_data='wallet')
    builder.row(cancel_button, width=1)


    return builder.as_markup()


def cancel_withdraw():
    builder = InlineKeyboardBuilder()

    cancel_button  = InlineKeyboardButton(text='❌ Cancel', callback_data='wallet')
    builder.row(cancel_button, width=1)

    return builder.as_markup()


def to_home():
    builder = InlineKeyboardBuilder()

    to_home_button  = InlineKeyboardButton(text='⬅ Back to Home', callback_data='home')
    builder.row(to_home_button, width=1)

    return builder.as_markup()


def settings_keyboard(settings: Settings):
    builder = InlineKeyboardBuilder()

    to_home  = InlineKeyboardButton(text='⬅ Back to Home', callback_data='home')
    builder.row(to_home, width=1)

    slippage_config = InlineKeyboardButton(text='Slippage', callback_data='slippage_config_none')
    builder.row(slippage_config, width=1)

    buy_slippage = InlineKeyboardButton(text=f'Buy: {settings.buy_slippage}%', callback_data='slippage_config_buy')
    sell_slippage = InlineKeyboardButton(text=f'Sell: {settings.sell_slippage}%', callback_data='slippage_config_sell')
    builder.row(buy_slippage, sell_slippage, width=2)

    extra_confirmation = InlineKeyboardButton(text='Extra confirmation', callback_data='none')
    builder.row(extra_confirmation, width=1)

    confirmation = InlineKeyboardButton(text=f'{"True" if settings.extra_confirmation else "False"}', callback_data='change_confirmation')
    builder.row(confirmation, width=1)

    return builder.as_markup()


def sell_keyboard(tokens):
    builder = InlineKeyboardBuilder()

    for token in tokens:
        mint, amount, symbol = token

        token_button = InlineKeyboardButton(text=f'{symbol} - {amount}', callback_data=f'show_sell_{mint}')
        builder.row(token_button, width=1)


    to_home  = InlineKeyboardButton(text='Close', callback_data='home')
    builder.row(to_home, width=1)

    return builder.as_markup()
        

def swap_confirmation():
    builder = InlineKeyboardBuilder()

    confirm_button = InlineKeyboardButton(text='Confirm ✅', callback_data=f'confirm_swap')
    builder.row(confirm_button, width=1)

    cancel_button  = InlineKeyboardButton(text='Cancel ❌', callback_data='home')
    builder.row(cancel_button, width=1)


    return builder.as_markup()


def sell_token(token_address):
    builder = InlineKeyboardBuilder()

    back_button = InlineKeyboardButton(text='⬅ Back', callback_data='sell')
    builder.row(back_button, width=1)

    _50_percent = InlineKeyboardButton(text='50%', callback_data=f'sell_{token_address}_50')
    _75_percent = InlineKeyboardButton(text='75%', callback_data=f'sell_{token_address}_75')
    _100_percent = InlineKeyboardButton(text='100%', callback_data=f'sell_{token_address}_100')
    builder.row(_50_percent, _75_percent, _100_percent, width=3)

    x_percent = InlineKeyboardButton(text='X % 🖊️', callback_data=f'sell_{token_address}_x')
    x_amount = InlineKeyboardButton(text='X Amount 🖊️', callback_data=f'sell_{token_address}_amount')
    builder.row(x_percent, x_amount, width=2)

    refresh_button = InlineKeyboardButton(text='🔄 Refresh', callback_data=f'show_sell_{token_address}')
    builder.row(refresh_button, width=1)

    return builder.as_markup()


def pump_keyboard(tokens: list[dict]):
    builder = InlineKeyboardBuilder()

    tokens.sort(key = lambda token: token['creation_time'])
    for token in tokens:
        if token.get('name'):

            creation_time = token['creation_time']
            mint, symbol = token['mint'], token['symbol']
            token_button = InlineKeyboardButton(text=f'{symbol} - {(datetime.now() - creation_time).seconds}s ago', callback_data=f'pump_{mint}')
            builder.row(token_button, width=1)

    refresh_button = InlineKeyboardButton(text='🔄 Refresh', callback_data='pump.fun')
    to_home = InlineKeyboardButton(text='To Home', callback_data='home')
    builder.row(refresh_button, to_home, width=2)

    return builder.as_markup()


def sniper_show_keyboar():
    builder = InlineKeyboardBuilder()

    lists = InlineKeyboardButton(text='⚡ List of Active Snipers', callback_data='sniper_list')
    close = InlineKeyboardButton(text='❌ Close', callback_data='home')

    builder.row(lists, close, width=1)

    return builder.as_markup()


def sniper_token(slippage, gas, amount, address, mev_protection):
    builder = InlineKeyboardBuilder()

    refresh = InlineKeyboardButton(text='🔄 Refresh', callback_data=f'snipe_{address}')
    builder.row(refresh, width=1)

    gas_button = InlineKeyboardButton(text=f'Gas: {gas} SOL', callback_data='sniper_gas')
    slippage_button = InlineKeyboardButton(text=f'Slippage: {slippage}%', callback_data='sniper_slippage')
    builder.row(gas_button, slippage_button, width=2)

    amount_button = InlineKeyboardButton(text=f'Amount: {amount} SOL', callback_data='sniper_amount')
    mev_protection_button = InlineKeyboardButton(text=f'MEV Protection: {"On" if mev_protection else "Off"}', callback_data='sniper_mev')
    builder.row(amount_button, mev_protection_button, width=2)

    create_snipe = InlineKeyboardButton(text='Create', callback_data='create_sniper')
    close = InlineKeyboardButton(text='❌ Close', callback_data='home')
    builder.row(create_snipe, close, width=2)

    return builder.as_markup()


def edit_sniper_token(slippage, gas, amount, mev_protection, order_id):
    builder = InlineKeyboardBuilder()

    gas_button = InlineKeyboardButton(text=f'Gas: {gas} SOL', callback_data='edit_sniper_gas')
    slippage_button = InlineKeyboardButton(text=f'Slippage: {slippage}%', callback_data='edit_sniper_slippage')
    builder.row(gas_button, slippage_button, width=2)

    amount_button = InlineKeyboardButton(text=f'Amount: {amount} SOL', callback_data='edit_sniper_amount')
    mev_protection_button = InlineKeyboardButton(text=f'MEV Protection: {"On" if mev_protection else "Off"}', callback_data='edit_sniper_mev')
    builder.row(amount_button, mev_protection_button, width=2)

    create_snipe = InlineKeyboardButton(text='Delete', callback_data=f'delete_sniper_{order_id}')
    close = InlineKeyboardButton(text='❌ Close', callback_data='sniper_list')
    builder.row(create_snipe, close, width=2)

    return builder.as_markup()


def cancel_sniper_config(address):
    builder = InlineKeyboardBuilder()

    cancel = InlineKeyboardButton(text='❌ Cancel', callback_data=f'snipe_{address}')
    builder.row(cancel, width=1)

    return builder.as_markup()


def show_all_snipers(orders: list[Order]):
    builder = InlineKeyboardBuilder()

    for order in orders:
        button = InlineKeyboardButton(text=f'{order.token_address}', callback_data=f'edit_sniper_show_{order.id}')
        builder.row(button, width=1)

    close = InlineKeyboardButton(text='❌ Close', callback_data='sniper_bot')
    builder.row(close, width=1)

    return builder.as_markup()