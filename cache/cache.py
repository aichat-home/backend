from typing import Any, Dict
from typing import Callable

import time

from functools import wraps


class SimpleCache:
    def __init__(self, echo: bool = True) -> None:
        self.cache: Dict[str, Any] = {}
        self.ttl: Dict[str, float] = {}
        self.echo = echo

    def set(self, key: str, value: Any, ttl: int):
        self.cache[key] = value
        self.ttl[key] = time.time() + ttl
        if self.echo:
            print(f'Set {key}: {value}')

    def get(self, key):
        if key in self.cache :
            if self.ttl[key] > time.time():
                if self.echo:
                    print(f'Get {key}: {self.cache[key]}')
                return self.cache[key]
            else:
                if self.echo:
                    print(f'Expired {key}, deleting')
                self.delete(key)
        return None
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            del self.ttl[key]



class CacheManager:
    def __init__(self, cache):
        self.cache: SimpleCache = cache

    def cache_response(self, key: str, ttl: int):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cached = self.cache.get(key)
                if cached:
                    return cached
                result = await func(*args, **kwargs)
                self.cache.set(key, result, ttl)
                return result
            return wrapper
        return decorator
