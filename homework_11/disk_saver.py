"""
Сохранение на диск
"""
import logging
import re
from mimetypes import guess_extension
from pathlib import Path

import config
from models import NewsData


class Saver:
    """
    Сохраняет новости на диске
    """
    _id_pattern = re.compile(r"(\d+). (\d+) .+")

    def __init__(self):
        self._root_dir_path = Path.cwd() / config.DIR_NAME

    def get_existing_ids(self) -> set[str]:
        """
        Находит в папке список уже существующих id
        По соглашению, формат записи папок с новостями происходит в формате:
            <номер по порядку>. <id новости>
            Например: "1. 67325487"
        """
        ids = set()
        if self._root_dir_path.exists():
            dirs = [f.name for f in self._root_dir_path.iterdir() if f.is_dir()]
            for dir_name in dirs:
                res = self._id_pattern.match(dir_name)
                if res is not None:
                    _id = res.group(2)
                    ids.add(_id)
        return ids

    def _get_max_number(self) -> int:
        """
        Находит максимальный порядковый номер
        """
        numbers = {0, }
        if self._root_dir_path.exists():
            dirs = [f.name for f in self._root_dir_path.iterdir() if f.is_dir()]
            for dir_name in dirs:
                res = self._id_pattern.match(dir_name)
                if res is not None:
                    number = res.group(1)
                    numbers.add(int(number))
        return max(numbers)

    def _create_root_dir_if_not_exists(self):
        """
        Создает корневую папку, если её еще нет
        """
        self._root_dir_path.mkdir(exist_ok=True)

    @staticmethod
    def _get_file_extension(news_data: NewsData) -> str:
        """
        Узнаем расширение файла по content_type от сервера
        """
        content_type = news_data.news_content_type
        content_type = content_type if content_type else ""
        extension = guess_extension(content_type)
        if extension is None:
            return ".html"
        return extension

    @staticmethod
    def _clean_news_name(news_name):
        """
        Очищает название статьи
        от недопустимых при сохранении на диск символов
        """
        # Убираем недопустимые символы для всех операционных систем
        news_name = re.sub(r'[\/:*?"<>|]', '', news_name)
        # Убираем недопустимые символы для Windows
        news_name = re.sub(r'[\x00-\x1f]', '', news_name)
        return news_name

    def save_news(self,
                  news_data: NewsData,
                  news_page: bytes | None,
                  comments_page: bytes | None):
        """
        Сохраняет страницы на диск
        """
        # Создаем корневую папку
        self._create_root_dir_if_not_exists()
        # Находим максимальный порядковый номер новости
        max_number = self._get_max_number()
        number = max_number + 1
        # Очищаем название новости от недопустимых символов
        news_name = self._clean_news_name(news_data.news_name)
        # Находим путь к папке с новостью
        dir_name = f"{number}. {news_data.news_id} {news_name}"
        dir_path = self._root_dir_path / dir_name
        # Создаем её
        dir_path.mkdir(exist_ok=True)
        # Узнаем расширение файла для страницы с новостью
        news_page_ext = self._get_file_extension(news_data)
        # Добавляем имена файлов к пути
        news_page_path = self._root_dir_path / dir_path / f"news_page{news_page_ext}"
        comments_page_path = self._root_dir_path / dir_path / "comments_page.html"
        # Сохраняем
        if news_page is not None:
            try:
                with open(news_page_path, "wb") as file:
                    file.write(news_page)
            except Exception as err:
                logging.error(f'Ошибка "{err}" при сохранения файла новости :: {news_page_path}')
        if comments_page is not None:
            try:
                with open(comments_page_path, "wb") as file:
                    file.write(comments_page)
            except Exception as err:
                logging.error(f'Ошибка "{err}" при сохранения файла с комментариями :: {news_page_path}')
