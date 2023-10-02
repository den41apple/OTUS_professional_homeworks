"""
Тестирование классов запроса
"""
import pytest

from api import (ClientsInterestsRequest,
                 OnlineScoreRequest,
                 MethodRequest)


class TestClientsInterestsRequest:
    _class = ClientsInterestsRequest

    @pytest.mark.parametrize("kwargs, exception", (
            ({"client_ids": [1, 2, 3]}, None),
            ({"date": "01.01.2020"}, ValueError),
    ))
    def test_required_fields(self, kwargs: dict, exception: Exception):
        """
        Тестирование обязательных к заполнению полей
        """
        if exception is None:
            self._class(**kwargs)
        else:
            with pytest.raises(exception):
                self._class(**kwargs)

    @pytest.mark.parametrize("kwargs, exception", (
            ({"client_ids": None, "date": "01.01.2020"}, ValueError),
            ({"client_ids": [1, 2], "date": None}, None),
    ))
    def test_not_nullable_fields(self, kwargs: dict, exception: Exception):
        """
        Тестирование на пустое значение поля
        """
        if exception is None:
            self._class(**kwargs)
        else:
            with pytest.raises(exception):
                self._class(**kwargs)


class TestOnlineScoreRequest:
    _class = OnlineScoreRequest

    @pytest.mark.parametrize("kwargs, exception", (
            ({"phone": "", "email": ""}, None),
            ({"first_name": "", "last_name": ""}, None),
            ({"birthday": "01.01.2020", "gender": 0}, None),
            ({"phone": None}, ValueError),
            ({"email": None}, ValueError),
            ({"first_name": None}, ValueError),
            ({"last_name": None}, ValueError),
            ({"birthday": None}, ValueError),
            ({"gender": None}, ValueError),
    ))
    def test_required_fields(self, kwargs: dict, exception: Exception):
        """
        Тестирование обязательных к заполнению полей
        """
        if exception is None:
            self._class(**kwargs)
        else:
            with pytest.raises(exception):
                self._class(**kwargs)

    @pytest.mark.parametrize("kwargs", (
            {"phone": None, "email": None},
            {"first_name": None, "last_name": None},
            {"birthday": None, "gender": None}
    ))
    def test_nullable_fields(self, kwargs: dict):
        """
        Тестирование на пустое значение поля
        """
        self._class(**kwargs)


class TestMethodRequest:
    _class = MethodRequest

    @pytest.mark.parametrize("kwargs, exception", (
            ({"login": "", "token": "", "arguments": {}, "method": ""}, None),
            ({"login": "", "token": "", "arguments": {}}, ValueError),
            ({"login": "", "token": "", "method": ""}, ValueError),
            ({"login": "", "arguments": {}, "method": ""}, ValueError),
            ({"token": "", "arguments": {}, "method": ""}, ValueError),
    ))
    def test_required_fields(self, kwargs: dict, exception: Exception):
        """
        Тестирование обязательных к заполнению полей
        """
        if exception is None:
            self._class(**kwargs)
        else:
            with pytest.raises(exception):
                self._class(**kwargs)

    @pytest.mark.parametrize("kwargs, exception", (
            ({"account": None, "login": "", "token": "", "arguments": {}, "method": ""}, None),
            ({"account": "", "login": None, "token": "", "arguments": {}, "method": ""}, None),
            ({"account": "", "login": "", "token": None, "arguments": {}, "method": ""}, None),
            ({"account": "", "login": "", "token": "", "arguments": None, "method": ""}, None),
            ({"account": "", "login": "", "token": "", "arguments": {}, "method": None}, ValueError),
    ))
    def test_nullable_fields(self, kwargs: dict, exception: Exception):
        """
        Тестирование на пустое значение поля
        """
        if exception is None:
            self._class(**kwargs)
        else:
            with pytest.raises(exception):
                self._class(**kwargs)
