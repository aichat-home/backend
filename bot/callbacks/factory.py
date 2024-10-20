from datetime import datetime

from aiogram.filters.callback_data import CallbackData




class TokenCallback(CallbackData, prefix='token_callback'):
    mint: str
    name: str
    symbol: str
    market_cap_sol: str
    v_sol_in_bonding_curve: float
    v_tokens_in_bondnig_curve: float
    creation_time: datetime
    trader_public_key: str