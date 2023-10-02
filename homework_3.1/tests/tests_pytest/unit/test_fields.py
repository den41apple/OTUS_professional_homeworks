"""
Тестирование полей
"""
import random
from datetime import datetime, timedelta

import pytest

from api import (FieldBase,
                 CharField,
                 ArgumentsField,
                 EmailField,
                 PhoneField,
                 DateField,
                 BirthDayField,
                 GenderField,
                 ClientIDsField)


class FieldTestBase:
    """
    Тестирование полей
    по одинаковому сценарию
    """
    _field = FieldBase
    _error_params = (None,)
    _no_error_params = (None,)

    @pytest.fixture(scope="function")
    def field(self):
        return self._field()

    def test_value_error(self, value, field):
        """
        Тестирование на вызов ValueError
        """
        with pytest.raises(ValueError):
            field.validate(value)

    def test_no_errors(self, value, field):
        """
        Тестирование на выполнение без ошибок
        """
        field.validate(value)


class TestCharField(FieldTestBase):
    """
    Тестирование CharField
    """
    _field = CharField
    _error_params = (1, {}, [], (), 2.)
    _no_error_params = ("1", "{}", "[]", "()", "2.")

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestArgumentsField(FieldTestBase):
    """
    Тестирование ArgumentsField
    """
    _field = ArgumentsField
    _error_params = ({1, 2}, dict, '1', [], (), 2.)
    _no_error_params = ({}, {1: 2}, {"1": 2})

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestEmailField(FieldTestBase):
    """
    Тестирование EmailField
    """
    _field = EmailField
    _error_params = ({1, 2}, dict, '1', [], (), 2.,
                     "example.mail.ru",
                     "example")
    _no_error_params = ("example@mail.ru",
                        "example33@mail.ru",
                        "example@mail22.com")

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestPhoneField(FieldTestBase):
    """
    Тестирование PhoneField
    """
    _field = PhoneField
    _error_params = ("99876536178",
                     1, "32423", "7985",
                     "7ХХХХХХХХХХ")
    _no_error_params = ("79859721894",
                        "77576435998",
                        "77560099868",
                        "79854568768")

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        if random.choice([True, False]):
            # Может быть и числом
            value = int(value)
        super().test_no_errors(value, field)


class TestDateField(FieldTestBase):
    """
    Тестирование DateField
    """
    _field = DateField
    _error_params = ("{1, 2}", "dict", '1', "[]", "()", "2.",
                     "example.mail.ru",
                     "example"
                     "2022.01.01",
                     "2022-01-01",
                     "0000-00-00")
    _no_error_params = ("01.12.2022",
                        "31.12.2022",
                        "01.01.1970")

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestBirthDayField(FieldTestBase):
    """
    Тестирование BirthDayField
    """
    _field = BirthDayField
    more_than_70_years = datetime.today() - timedelta(days=365 * random.randint(71, 100))
    more_than_70_years = more_than_70_years.strftime("%d.%m.%Y")
    _error_params = ("{1, 2}", "dict", '1', "[]", "()", "2.",
                     "example.mail.ru",
                     "example"
                     "2022.01.01",
                     "2022-01-01",
                     "0000-00-00",
                     more_than_70_years)
    # Сформируем рандомный список дат до 70-и лет от сегодняшнего дня
    _no_error_days = (datetime.today()
                      - timedelta(days=365 * random.randint(0, 70))
                      + timedelta(days=random.randint(0, 365))
                      for _ in range(10))
    _no_error_params = (day.strftime("%d.%m.%Y") for day in _no_error_days)

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestGenderField(FieldTestBase):
    """
    Тестирование GenderField
    """
    _field = GenderField
    _error_params = (100, 200, 300, "11")
    _no_error_params = (0, 1, 2)

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)


class TestClientIDsField(FieldTestBase):
    """
    Тестирование ClientIDsField
    """
    _field = ClientIDsField
    _error_params = (100, 200, 300, "11", {}, {1: 2}, {1, 2}, ["33"],
                     (1, 2, 3), [dict])
    _no_error_params = ([], [12, 3], [33])

    @pytest.mark.parametrize("value", _error_params)
    def test_value_error(self, value, field):
        super().test_value_error(value, field)

    @pytest.mark.parametrize("value", _no_error_params)
    def test_no_errors(self, value, field):
        super().test_no_errors(value, field)
