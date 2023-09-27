#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import re
import uuid
from copy import deepcopy
from optparse import OptionParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Type

from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class FieldBase:
    """Базовый класс"""

    def __init__(self, required: bool = True, nullable: bool = False):
        self.required = required
        self.nullable = nullable
        self._value = None
        self.name = None  # Имя поля

    def validate(self, value) -> Any:
        if self.required and value is None:
            raise ValueError(f'Поле {self.name} обязательно')
        if not self.nullable and not value:
            raise ValueError(f'Поле {self.name} должно быть не пустым')
        return value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.validate(value)

    def __str__(self):
        return repr(self._value)

    def __repr__(self):
        return str(self)


class CharField(FieldBase):
    """Строковое поле"""

    def validate(self, value: str | None) -> str | None:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValueError("Должно быть строкой")
            self._value = value
            return self._value


class ArgumentsField(FieldBase):
    """Словарь (объект в терминах json)"""

    def validate(self, value: dict | None) -> dict | None:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, dict):
                raise ValueError("Должно быть словарем")
            self._value = value
            return self._value


class EmailField(CharField):
    """Строка, в которой есть @"""

    def validate(self, value: str | None) -> str | None:
        value = super().validate(value)
        if value is not None:
            if "@" not in value:
                raise ValueError("Неверный формат e-mail")
            return self._value


class PhoneField(FieldBase):
    """
    Строка или число, длиной 11, начинается с 7
    """
    __pattern = re.compile(r'7\d{10}')

    def validate(self, value: str | int | None) -> str | None:
        value = super().validate(value)
        if value is not None:
            value = str(value)
            values = self.__pattern.findall(value)
            if len(values) != 1:
                raise ValueError("Номер телефона должен быть в формате 7ХХХХХХХХХХ")
            self._value = values[0]
            return self._value


class DateField(FieldBase):
    """Дата в формате DD.MM.YYYY"""

    def validate(self, value: str | None) -> Type[datetime.datetime] | None:
        value = super().validate(value)
        if value is not None:
            try:
                self._value = datetime.datetime.strptime(value, "%d.%m.%Y").date()
            except ValueError as err:
                raise ValueError("Дата должна быть в формате DD.MM.YYYY") from err
            return self._value


class BirthDayField(DateField):
    """
    Дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет
    """

    def validate(self, value: str | None) -> Type[datetime.datetime] | None:
        if value is not None:
            value: datetime = super().validate(value)
            today = datetime.datetime.today().date()
            diff_years = (today - value).days / 365
            if diff_years > 70:
                raise ValueError("Со дня рождения не должно пройти более 70 лет")
            self._value = value
            return self._value


class GenderField(FieldBase):
    """
    Пол как число 0, 1 или 2
    """

    def validate(self, value: int | None) -> int:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, int):
                raise ValueError("Пол должен быть целым числом")
            if value not in GENDERS:
                raise ValueError("Неверное значение пола")
            self._value = value
            return self._value


class ClientIDsField(FieldBase):
    """Массив чисел"""

    def validate(self, value: list[int] | None) -> list[int] | None:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("Должно быть массивом")
            [self._check(el) for el in value]
            self._value = value
            return self._value

    def _check(self, el):
        if not isinstance(el, int):
            raise ValueError("Должно быть числом")


class RequestMeta(type):
    """
    Мета класс для сбора всех атрибутов при создании
    """

    def __new__(cls, name: str, bases: tuple, attrs: dict):
        _fields = {}
        _attrs = deepcopy(attrs)
        for key, value in attrs.items():
            if isinstance(value, FieldBase):
                _fields[key] = value
                _attrs.pop(key)
        _attrs['_fields'] = _fields
        new_class = super().__new__(cls, name, bases, _attrs)
        return new_class


class RequestBase(metaclass=RequestMeta):
    """Базовый класс для запросов"""

    def __init__(self, **kwargs):
        # Установим атрибуты
        for attr_name, instance in self._fields.items():
            value = kwargs.get(attr_name)
            instance.name = attr_name
            instance.value = value
            setattr(self, attr_name, value)

    def validate(self):
        errors_fields = []
        for field_name, field in self._fields.items():
            value = getattr(self, field_name)
            if value is None and (field.nullable is False or field.required is True):
                errors_fields.append(field_name)
        if errors_fields:
            raise ValueError(f'Поле(я) "{", ".join(errors_fields)}" необходимо(ы) и не должно(ы) быть None')

    def dict(self) -> dict:
        return self._fields


class ClientsInterestsRequest(RequestBase):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(RequestBase):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        error_message = ("Необходима хотя бы одна пара из: "
                         "phone-email, first_name-last_name, gender-birthday")
        if not (
                (self.phone and self.email)
                or (self.first_name and self.last_name)
                or (self.birthday and self.gender in GENDERS)
        ):
            raise ValueError(error_message)


class MethodRequest(RequestBase):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request: MethodRequest):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def online_score_handler(request: MethodRequest,
                         ctx: dict,
                         store) -> tuple[dict, int]:
    """
    Обработчик "online_score"
    """
    if request.is_admin:
        score = 42
        return {'score': score}, OK
    arguments = request.arguments or {}
    try:
        r = OnlineScoreRequest(**arguments)
        r.validate()
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST
    ctx['has'] = arguments.keys()
    score = get_score(store, **r.dict())
    return {'score': score}, OK


def clients_interests_handler(request: MethodRequest,
                              ctx: dict,
                              store) -> tuple[dict, int]:
    """
    Обработчик "clients_interests"
    """
    arguments = request.arguments or {}
    try:
        request = ClientsInterestsRequest(**arguments)
        request.validate()
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST
    interests = {}
    for client_id in request.client_ids:
        interests[f'client_id{client_id}'] = get_interests('nowhere_store',
                                                           client_id)
    ctx["nclients"] = len(arguments.get("client_ids", []))
    return interests, OK


def method_handler(request: dict,
                   ctx: dict,
                   store) -> tuple[dict, int]:
    response, code = None, None
    methods = {'clients_interests': clients_interests_handler,
               'online_score': online_score_handler}
    try:
        request = MethodRequest(**request.get('body'))
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST
    if not request.method:
        return {
            'code': INVALID_REQUEST,
            'error': 'INVALID_REQUEST'
        }, INVALID_REQUEST
    if not check_auth(request):
        return {
            'code': FORBIDDEN,
            'error': "Forbidden"
        }, FORBIDDEN
    method = methods[request.method]
    response, code = method(request, ctx, store)
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
