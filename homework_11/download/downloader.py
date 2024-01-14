"""
Загрузка новостей и комментариев
"""
import asyncio
import logging

from aiohttp.client_exceptions import ClientConnectorError

import config
from disk_saver import Saver
from models import NewsData
from .get_page import get_page
from .main_page_data_fetcher import MainPageDataFetcher


class Downloader:
    """
    Производит загрузку новостей и комментариев
    """

    def __init__(self):
        # Объект для работы с диском
        self.saver = Saver()
        # Извлечение данных о новостях с главной страницы
        self.fetch_main_page_news_data = MainPageDataFetcher()

    async def download(self):
        """
        Порядок загрузки данных
        """
        # Получение уже сохраненных на диске id
        exists_ids: set[str] = self.saver.get_existing_ids()
        # Извлечение данных о новостях
        news_data_list: list[NewsData] = await self.fetch_main_page_news_data()
        # Фильтрация id, оставляем только новые для нас
        news_data_list = self._filter_ids(news_data_list, exists_ids)
        if not news_data_list:
            logging.info("Нет новостей для загрузки")
            return
        # Загрузка страниц новостей и комментариев
        tasks = []
        cnt = 0
        for i, news_data in enumerate(news_data_list):
            if cnt == config.POOL_SIZE:
                cnt = 0
                await asyncio.gather(*tasks)
                tasks.clear()
            tasks.append(self._download_one_news(i, news_data, news_data_list))
            cnt += 1
        await asyncio.gather(*tasks)

    async def _download_one_news(self, i, news_data, news_data_list):
        """
        Загружает одну новость
        """
        current_element = f"[{i + 1}/{len(news_data_list)}]"
        # Загрузка страницы с новостью
        logging.info(f'Новость {current_element}: "{news_data.news_name}"')
        try:
            news_page = await self._download_news_page(news_data)
        except ClientConnectorError:
            logging.error(f'Ошибка при загрузке страницы с новостью {current_element}: '
                          f'"{news_data.news_name}"')
            news_page = None
        # Загрузка страницы с комментариями
        try:
            comments_page = await self._download_comments_page(news_data)
        except ClientConnectorError:
            logging.error(f'Ошибка при загрузке страницы с комментариями {current_element}: '
                          f'"{news_data.news_name}"')
            comments_page = None
        # Сохранение страниц на диск
        self.saver.save_news(news_data, news_page, comments_page)

    @staticmethod
    def _filter_ids(news_data_list: list[NewsData], exists_ids: set[str]) -> list[dict]:
        """
        Отсеивает новости с существующими id
        И разворачивает список для сохранения в правильном порядке
        """
        return [el for el in news_data_list
                if str(el.news_id) not in exists_ids][::-1]

    async def _download_news_page(self, news_data: NewsData) -> bytes | None:
        """
        Загружает страницу с новостью
        """
        url = news_data.news_page_url
        response = await get_page(url)
        news_data.news_content_type = response.get("headers", {}).get("Content-Type")
        return response.get("content")

    async def _download_comments_page(self, news_data: NewsData) -> bytes | None:
        """
        Загружает страницу с комментариями
        """
        url = news_data.comments_page_url
        if url is None:
            return
        response = await get_page(url)
        return response.get("content")
