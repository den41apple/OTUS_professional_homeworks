"""
Тесты функций
"""
import fakeredis
import pytest

from store import Store, RedisClient
from scoring import get_score, get_interests

class TestFunctions:

    @pytest.fixture(scope="function")
    def store(self) -> Store:
        self._fake_server = fakeredis.FakeServer(version=7)
        storage = RedisClient(client=fakeredis.FakeRedis, client_kwargs={"server": self._fake_server})
        return Store(storage=storage)

    def test_no_errors_get_score_without_connection(self, store: Store):
        """
        Функции "get_score" не важна доступность store'а, она использует
        его как кэш и, следовательно, должна работать даже если store сгорел в
        верхних слоях атмосферы
        """
        self._fake_server.connected = False
        get_score(store=store, phone="78986473892", email="examlpe@mail.ru")

    def test_errors_get_interests_without_connection(self, store: Store):
        """
        Функция "get_interests" использует store как персистентное
        хранилище и если со store'ом что-то случилось, может отдавать только
        ошибки
        """
        self._fake_server.connected = False
        with pytest.raises(ConnectionError):
            get_interests(store=store, cid=1)

