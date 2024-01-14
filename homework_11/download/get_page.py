"""
Получение страницы по URL
"""
from asyncio.exceptions import TimeoutError
from typing import Any

import aiohttp


async def get_page(url: str) -> dict[str, Any]:
    """
    Получает страницу по url
    """
    timeout = aiohttp.ClientTimeout(10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                return {"content": await response.content.read(),
                        "headers": response.headers}
    except TimeoutError:
        return {}
