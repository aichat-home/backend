from hashlib import sha256
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import HTTPException, status, Header
from core import settings



def validate_dependency(User_Init_Data: str = Header(None)):
    if not User_Init_Data or not validate_init_data(settings.telegram_token, User_Init_Data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid telegram init data'
        )
    result = {}
    for key, value in parse_qsl(User_Init_Data):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            result[key] = value
        else:
            result[key] = value
    return result.get('user')


def validate_init_data(token, raw_init_data):
    try:
        parsed_data = dict(parse_qsl(raw_init_data))
    except ValueError:
        return False
    if "hash" not in parsed_data:
        return False

    init_data_hash = parsed_data.pop('hash')
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed_data.items()))
    secret_key = hmac.new(key=b"WebAppData", msg=token.encode(), digestmod=sha256)

    return hmac.new(secret_key.digest(), data_check_string.encode(), sha256).hexdigest() == init_data_hash



def sniper_service_validate(x_access_token: str = Header(None)):
    if x_access_token != settings.sniper_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized'
        )
    return True