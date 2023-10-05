"""
Переменные конфигурации
"""
import logging
from argparse import ArgumentParser, Namespace

_argument_parser = ArgumentParser()

NUM_WORKERS = 30
IP_ADDR = "0.0.0.0"
PORT = 80
BUFFER_SIZE = 1_024
METHODS = 'GET|HEAD'
DOCUMENT_ROOT = "tests"
SERVER_NAME = "http_server"
LOG_LEVEL = "WARNING"


def init_argument_parser():
    """
    Инициализация парсера аргументов
    """
    _argument_parser.add_argument("-w", "--workers",
                                  help="Количество обработчиков",
                                  type=int,
                                  default=NUM_WORKERS)
    _argument_parser.add_argument("-r", "--root",
                                  help="Корневая директория",
                                  type=str,
                                  default=DOCUMENT_ROOT)
    _argument_parser.add_argument("-p", "--port",
                                  help="Номер порта",
                                  type=int,
                                  default=PORT)
    _argument_parser.add_argument("-l", "--log",
                                  help="Уровень логирования",
                                  type=str,
                                  default=LOG_LEVEL)
    _update_config()


def _update_config():
    """
    Обновляет переменные конфигурации
    """
    global NUM_WORKERS, DOCUMENT_ROOT, PORT, LOG_LEVEL
    args: Namespace = _argument_parser.parse_args()
    NUM_WORKERS = args.workers
    DOCUMENT_ROOT = args.root
    PORT = args.port
    LOG_LEVEL = args.log.upper()


def init_logging():
    """Настройка логирования"""
    logging.basicConfig(level=LOG_LEVEL,
                        format='[%(asctime)s] %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
