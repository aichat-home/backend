from datetime import datetime, timezone
from aiohttp import ClientSession

import websockets
from collections import deque
import json

from spl.token.constants import WRAPPED_SOL_MINT

from utils import market
from rpc import client


# A deque to store the last 20 messages
last_20_data = deque(maxlen=20)

async def websocket_handler():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        while True:
            payload = {
                "method": "subscribeNewToken",
            }
            await websocket.send(json.dumps(payload))

            async for message in websocket:
                data = json.loads(message)
                data['creation_time'] = datetime.now()
                last_20_data.append(data)


async def get_pump_token_info(client_session: ClientSession, mint: str) -> dict | None:
    url = f'https://frontend-api.pump.fun/coins/{mint}'
    async with client_session.get(url) as response:
        if response.status == 200:
            token_data = await response.json()
            if token_data.get('name'):
                decimals = await market.get_token_decimals(client, token_data['mint'])
                token_data['decimals'] = decimals

                return get_pumpfun_need_data(token_data)
            return None
        else:
            return None


def human_readable(num, precision=20):
    # Format the number with the specified precision
    # If the number is very small (scientific notation), convert to decimal notation
    if num < 1e-6:
        return f"{num:.{precision}f}"
    else:
        return f"{num:.{precision}g}"   



def get_pumpfun_need_data(token_data: dict) -> dict:
    time_passed = datetime.now(timezone.utc) - datetime.fromtimestamp(token_data['created_timestamp'] / 1000, tz=timezone.utc)

    if time_passed.days >= 1:
        time_passed = f'{time_passed.days} days ago'
    elif time_passed.seconds / 3600 >= 1:
        time_passed = f'{time_passed.seconds // 3600} hours ago'
    elif time_passed.seconds / 60 >= 1:
        time_passed = f'{time_passed.seconds // 60} minutes ago'
    else:
        time_passed = f'{time_passed.seconds} seconds ago'


    return {
        'address': token_data['mint'],
        'name': token_data['name'],
        'symbol': token_data['symbol'],
        'creator': token_data['creator'],
        'time_passed': time_passed,
        'total_supply': token_data['total_supply'],
        'market_cap_sol': token_data['market_cap'],
        'usd_market_cap': token_data['usd_market_cap'],
        'price': human_readable(token_data['usd_market_cap'] / (token_data['total_supply'] / token_data['decimals'])),
    }


# Function to retrieve the last 20 messages
def get_last_20_tokens():
    return list(last_20_data)
