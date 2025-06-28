import logging
from typing import Any, Dict

from bs4 import BeautifulSoup


class PageParseError(Exception):
    pass


logger = logging.getLogger(__name__)


def parse_page(
        html_content: str, 
        url: str, 
        encoding: str = 'utf-8'
        ) -> Dict[str, Any]:
    try:
        logger.debug(f"Парсинг страницы: {url}")
        soup = BeautifulSoup(
            html_content, 
            'html.parser'
            )
        
        description_tag = soup.find('meta', attrs={"name": "description"})
        description = description_tag.get(
            'content', ''
            ).strip() if description_tag else None

        return {
            'h1': soup.find('h1').text.strip() if soup.find('h1') else None,
            'title': soup.title.string.strip() if soup.title else None,
            'description': description
        }
    except Exception as e:
        logger.error(f"Ошибка парсинга {url}: {e}")
        raise PageParseError(f"Ошибка парсинга страницы {url}: {e}")