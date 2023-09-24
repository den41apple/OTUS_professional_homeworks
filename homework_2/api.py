#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import re
import uuid
from optparse import OptionParser
from http.server import BaseHTTPRequestHandler, HTTPServer

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

    def _parse(self, value):
        return value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self._parse(value)


class CharField(FieldBase):
    """Строковое поле"""

    def _parse(self, value: str) -> str:
        value = super()._parse(value)
        if not isinstance(value, str):
            raise ValueError("Должно быть строкой")
        self._value = value
        return self._value


class ArgumentsField(FieldBase):
    """Словарь (объект в терминах json)"""

    def _parse(self, value: dict) -> dict:
        value = super()._parse(value)
        if not isinstance(value, dict):
            raise ValueError("Должно быть словарем")
        self._value = value
        return self._value


class EmailField(CharField):
    """Строка, в которой есть @"""

    def _parse(self, value: str) -> str:
        value = super()._parse(value)
        if not isinstance(value, str):
            raise ValueError("E-mail должен быть строкой")
        if not "@" in value:
            raise ValueError("Неверный формат e-mail")
        return self._value


class PhoneField(FieldBase):
    """
    Строка или число, длиной 11, начинается с 7
    """
    __pattern = re.compile(r'7\d{10}')

    def _parse(self, value: str | int) -> str:
        value = super()._parse(value)
        value = str(value)
        values = self.__pattern.findall(value)
        if len(values) != 1:
            raise ValueError("Номер телефона должен быть в формате 7ХХХХХХХХХХ")
        self._value = values[0]
        return self._value


class DateField(FieldBase):
    """Дата в формате DD.MM.YYYY"""
    __pattern = "%d.%m.%Y"

    def _parse(self, value: str) -> datetime:
        value = super()._parse(value)
        try:
            self._value = datetime.datetime.strptime(value, self.__pattern).date()
        except ValueError:
            raise ValueError("Дата должна быть в формате DD.MM.YYYY")
        return self._value


class BirthDayField(DateField):
    """
    Дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет
    """
    def _parse(self, value: str) -> datetime:
        value: datetime = super()._parse(value)
        today = datetime.datetime.today()
        diff_years = (today - value).days / 365
        if diff_years > 70:
            raise ValueError("Со дня рождения не должно пройти более 70 лет")
        self._value = value
        return self._value


class GenderField(FieldBase):
    """
    Число 0, 1 или 2
    """
    def _parse(self, value: int) -> int:
        value = super()._parse(value)
        if not isinstance(value, int):
            raise ValueError("Пол должен быть целым числом")
        if value not in [UNKNOWN, MALE, FEMALE]:
            raise ValueError("Неверное значение пола")
        self._value = value
        return self._value


class ClientIDsField(FieldBase):
    """Массив чисел"""

    def _parse(self, value: int) -> int:
        value = super()._parse(value)
        [self._check(el) for el in value]
        self._value = value
        return self._value

    def _check(self, el):
        if not isinstance(el, int):
            raise ValueError("Должно быть числом")



class ClientsInterestsRequest:
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest:
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest:
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
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
