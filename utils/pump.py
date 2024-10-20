from datetime import datetime

import websockets
from collections import deque
import json


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


# Function to retrieve the last 20 messages
def get_last_20_tokens():
    return list(last_20_data)
