import pytest
import fakeredis

from store import Store, RedisClient


class TestStore:

    @pytest.fixture(scope="function")
    def store(self) -> Store:
        self._fake_server = fakeredis.FakeServer(version=7)
        storage = RedisClient(client=fakeredis.FakeRedis, client_kwargs={"server": self._fake_server})
        return Store(storage=storage)

    def test_set_get(self, store: Store):
        """
        Проверка работы методов get и set
        """
        self._fake_server.connected = True
        store.set(key="foo", value="bar")
        assert store.get(key="foo"), b"bar"
        store.cache_set(key="foo", value="bar")
        assert store.cache_get(key="foo"), b"bar"

    def test_connection_error(self, store: Store):
        """
        Проверка на вызов исключения о проблемах с подключением
        """
        self._fake_server.connected = False
        with pytest.raises(ConnectionError):
            store.get(key="foo")
        self._fake_server.connected = True
        store.get(key="foo")

    def test_cache_set_get_no_error_without_connection(self, store: Store):
        """
        При cache_set и cache_get не должно быть исключений
        В случае утери соединения
        """
        self._fake_server.connected = False
        store.cache_set(key="foo", value="bar")
        store.cache_get(key="foo")
