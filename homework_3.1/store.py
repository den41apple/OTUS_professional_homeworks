"""
Работа с кешем Redis
"""
from functools import wraps
from typing import Any, Callable

import redis

def retry(num_retries: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for _ in range(num_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except (TimeoutError, ConnectionError) as err:
                    pass
            raise ConnectionError(f"Соединение прервано после {num_retries} попыток")

        return wrapper

    return decorator


class RedisClient:

    def __init__(self,
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 timeout: int = 3):
        self._host = host
        self._port = port
        self._db = db
        self._timeout = timeout
        self._client = None
        self._make_client()

    def _make_client(self) -> redis.Redis:
        """Создание клиента"""
        self._client = redis.Redis(host=self._host,
                                   port=self._port,
                                   db=self._db,
                                   socket_connect_timeout=self._timeout,
                                   socket_timeout=self._timeout,
                                   decode_responses=True)
        return self._client

    def set(self, key, value, expires: int = None) -> None:
        """Установка значения"""
        try:
            return self._client.set(key, value, ex=expires)
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except:
            raise ConnectionError

    def get(self, key) -> Any:
        """Получение значения по ключу"""
        try:
            value = self._client.get(key)
            if value is not None:
                return value
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except:
            raise ConnectionError


class Store:
    max_retries = 5

    def __init__(self):
        self._storage = RedisClient()

    @retry(max_retries)
    def get(self, key, use_cache_if_error=True):
        """
        Получение значения из кеша по ключу
        """
        if use_cache_if_error:
            try:
                return self._storage.get(key)
            except:
                return self.cache_get(key)
        else:
            return self._storage.get(key)

    @retry(max_retries)
    def set(self, key, value):
        """
        Установка значения
        """
        return self._storage.set(key, value)

    @retry(max_retries)
    def cache_get(self, key):
        """
        Получение значения из кеша по ключу
        """
        return self._storage.get(key)

    @retry(max_retries)
    def cache_set(self, key, value, expires: int = None):
        """
        Установка значения в кеш
        """
        self._storage.set(key, value, expires)
