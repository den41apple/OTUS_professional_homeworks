"""
Извлекает информацию о новостях с главной страницы
"""
import bs4

from models import NewsData
from .get_page import get_page


class MainPageDataFetcher:
    """
    Загружает главную страницу
    И извлекает список с данными новостей
    """
    url = "https://news.ycombinator.com/"

    def __init__(self):
        self._rows = None
        self._soup = None

    async def __call__(self) -> list[NewsData]:
        """
        Загружает список новостей
        """
        await self._get_main_page()
        self._find_rows()
        news_data_list = self._parse_news()
        return news_data_list

    async def _get_main_page(self):
        """
        Получает главную страницу
        """
        response = await get_page(self.url)
        response_string = response["content"]
        self._soup = bs4.BeautifulSoup(response_string, "html.parser")
        return self._soup

    def _find_rows(self) -> list:
        """
        Ищет все строки с новостями
        """
        table_general = self._soup.find_all("table", {"id": "hnmain"})
        tables = table_general[0].find_all("table")
        table = tables[1]
        self._rows = table.find_all("tr", recursive=False)
        self._rows = self._rows[:90]  # Должно быть по 3 строки на новость, новостей 30
        if len(self._rows) != 90:
            raise ValueError(f"Количество строк меньше 90 :: {len(self._rows)}")
        return self._rows

    def _parse_news(self) -> list[NewsData]:
        """
        Парсит новости
        """

        def get_class(string) -> str:
            """
            Извлекает атрибут class
            """
            try:
                return string.get("class")[0]
            except TypeError:
                return ""

        cnt = 0
        news_data_list = []
        _news_data = {}

        for i, row in enumerate(self._rows):
            cnt += 1
            _class = get_class(row)
            if _class == "athing":
                _news_data.update(self._parse_news_data(row))
            elif _class == "spacer":
                pass
            else:
                _news_data.update(self._get_comment_url(row))
            if cnt == 3:
                cnt = 0
                news_data = NewsData(**_news_data)
                news_data_list.append(news_data)
                _news_data = {}
        return news_data_list

    def _parse_news_data(self, row) -> dict:
        """
        Извлекает данные по каждой новости
        """
        titleline = row.find_all("span", {"class": "titleline"})[0]
        titleline_a = titleline.find_all("a", recursive=False)[0]
        href = titleline_a.get("href")
        if not href.startswith("http"):
            href = self.url + href
        return {"news_page_url": href,  # Ссылка на новость
                "news_name": titleline_a.get_text(),  # Название новости
                "news_id": row.get("id")}  # id новости

    def _get_comment_url(self, row) -> dict:
        """
        Извлекает url комментариев
        """
        href = None
        subline = row.find_all("span", {"class": "subline"})
        if len(subline) != 0:  # Если комментарии есть
            subline = subline[0]
            subline_a = subline.find_all("a", recursive=False)[-1]
            href = subline_a.get("href")
            if not href.startswith("http"):
                href = self.url + href
        return {"comments_page_url": href}  # Ссылка на комментарии
