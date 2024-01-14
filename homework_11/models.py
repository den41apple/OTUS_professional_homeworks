"""
Модель данных для каждой новости
"""
from dataclasses import dataclass


@dataclass
class NewsData:
    news_id: str = None
    news_name: str = None
    news_content_type: str = None
    news_page_url: str = None
    comments_page_url: str | None = None
