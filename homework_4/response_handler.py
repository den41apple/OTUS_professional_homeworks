"""
Формирование ответа
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from constants import content_types, response_codes, response_messages
from config import DOCUMENT_ROOT, SERVER_NAME


class ResponseHandler:

    def __init__(self):
        self._method = None
        self._path = None
        self._content_type = None
        self.status = None
        self._root = Path(__file__).parent / DOCUMENT_ROOT

    def process(self, method, path) -> str:
        """
        Обработка запроса
        """
        self._method = method
        self._path = path
        try:
            path = self._parse_path()
            self._content_type = self._get_content_type(path)
            with open(path, 'rb') as file:
                content = file.read()
            return self._make_response('OK', content)
        except ValueError as err:
            logging.error(f"Ошибка при обработке запроса: {err}")
            return self.error(str(err))

    def error(self, value) -> str:
        """
        Обработка ошибки
        """
        self._content_type = content_types.get('html')
        self._method = 'GET'
        code = response_codes.get(value)
        message = response_messages.get(value)
        description = f'{code} {message}'
        content = (f"<html><head><title>{description}</title></head>"
                   f"<body><h1>{description}</h1><hr/>"
                   f"{SERVER_NAME}</body></html>")
        return self._make_response(value, content.encode())

    def _make_response(self, value: str, content: bytes) -> str:
        """
        Формирование ответа
        """
        code = response_codes.get(value)
        message = response_messages.get(value)
        self.status = f"{code} {message}"
        utcnow = datetime.utcnow()
        utcnow = utcnow.strftime("%a, %d %b %Y %H:%M:%S %Z GMT")
        headers = [f'HTTP/1.1 {self.status}',
                   f'Date: {utcnow}',
                   f'Server: {SERVER_NAME}',
                   f'Content-Type: {self._content_type}',
                   f'Content-Length: {len(content)}',
                   'Connection: close']
        if self._method == 'GET':
            if 'text' in self._content_type:
                content = content.decode('UTF-8')
            headers.append(f'\r\n{content}')
        headers.append('\r\n')
        return '\r\n'.join(headers)

    @staticmethod
    def _get_content_type(path: str) -> str:
        """
        Получение content type для ответа
        """
        _, extension = os.path.splitext(path)
        extension = extension.replace('.', '')
        return content_types.get(extension, 'application/octet-stream')

    def _parse_path(self) -> str:
        """
        Формирование пути до файла
        """
        path = Path(self._root) / self._path[1:]
        path = Path(os.path.normpath(path))
        if str(self._root) not in str(path):
            raise ValueError('FORBIDDEN')
        index_path = path / "index.html"
        if (
                not path.exists()
                or path.is_file() and self._path[-1] == '/'
                or path.is_dir() and not index_path.exists()
        ):
            raise ValueError('NOT_FOUND')
        return path if path.is_file() else index_path
