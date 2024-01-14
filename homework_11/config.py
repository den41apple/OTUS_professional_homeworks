"""
Когнфигурация
"""
import logging
from optparse import OptionParser

# Кол-во одновременных загрузок
POOL_SIZE = 5
# Имя корневой папки
DIR_NAME = "news"
# Время ожидания перед следующим циклом загрузки
DELAY_SECONDS = 10


def init():
    _init_logging()
    _parse_args()


def _init_logging():
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


def _parse_args():
    global POOL_SIZE, DIR_NAME, DELAY_SECONDS
    op = OptionParser()
    op.add_option('--pool_size', action="store", type=int, default=POOL_SIZE,
                  metavar=POOL_SIZE,
                  help=f'Кол-во одновременных загрузок, по умолчанию {POOL_SIZE}')
    op.add_option('-d', '--dir', action="store", type=str, default=DIR_NAME,
                  metavar=DIR_NAME,
                  help=f'Имя папки, по умолчанию "{DIR_NAME}"')
    op.add_option('--delay_seconds', action="store", type=int, default=DELAY_SECONDS,
                  metavar=DELAY_SECONDS,
                  help=f'Количество секунд через которое будет повторятся загрузка, по умолчанию {DELAY_SECONDS}')
    (opts, args) = op.parse_args()

    POOL_SIZE = opts.pool_size
    DIR_NAME = opts.dir
    DELAY_SECONDS = opts.delay_seconds
    logging.info(f"ПАРАМЕТРЫ ЗАПУСКА: POOL_SIZE={POOL_SIZE}  DIR_NAME={DIR_NAME}  DELAY_SECONDS={DELAY_SECONDS}")
