"""
Обработка запроса
"""
import logging
import re
from queue import Queue
from socket import socket
from urllib.parse import unquote

from config import METHODS, BUFFER_SIZE
from response_handler import ResponseHandler


class RequestHandler:

    def __init__(self, index: int, connection_queue: Queue):
        self._index = index
        self._queue = connection_queue
        self._socket = None
        self._method = None
        self._path = None
        self._response_handler = ResponseHandler()
        self.start()

    def start(self):
        """
        Получение очереди подключений
        """

        while True:
            self._socket: socket = self._queue.get()
            self._read_from_socket()
            if self._parse_request():
                response = self._response_handler.process(self._method, self._path)
            else:
                response = self._response_handler.error('NOT_ALLOWED')
            logging.info(f"Thread {self._index}: Response ({self._response_handler.status})")
            self._socket.sendall(response.encode())
            self._socket.close()
            self._queue.task_done()

    def _read_from_socket(self) -> str:
        """
        Чтение из сокета
        """
        self._data = b''
        while True:
            part = self._socket.recv(BUFFER_SIZE)
            self._data += part
            if not part or b'\r\n\r\n' in part:
                break
        logging.info(f"Thread {self._index}: Получено {len(self._data)} байт")
        self._data = self._data.decode('UTF-8')
        return self._data

    def _parse_request(self) -> bool:
        """
        Обработка строки запроса
        """
        try:
            match = re.findall(rf"^({METHODS}) (\S+) HTTP", self._data)
            if match:
                match = match[0]
                path = unquote(match[1])
                self._path = path.split('?')[0]
                self._method = match[0]
                return True
        except:
            logging.warning(f"Thread {self._index}: Headers error: {self._data.splitlines()[0]}")
        return False
