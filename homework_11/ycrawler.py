"""
Основной модуль
"""
import asyncio
import logging
import time

import config
from config import init
from download.downloader import Downloader


async def cycle():
    """
    Цикл загрузки
    """
    logging.info("Загрузка начата")
    start_time = time.time()
    downloader = Downloader()
    await downloader.download()
    end_time = time.time()
    worked_time = end_time - start_time
    logging.info(f"Загрузка завершена, время выполнения {int(worked_time)} секунд")


async def main():
    logging.info("Crawler запущен")
    while True:
        logging.info(f"-" * 50)
        await cycle()
        # Засыпаем, ожидая следующего цикла загрузки
        logging.info(f"Ждем {config.DELAY_SECONDS} секунд До следующего цикла")
        await asyncio.sleep(config.DELAY_SECONDS)


if __name__ == '__main__':
    init()
    asyncio.run(main())
