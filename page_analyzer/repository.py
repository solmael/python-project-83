import logging
from typing import Dict, List, Optional

import requests
from psycopg2 import connect
from psycopg2.extras import DictCursor

from .parser import parse_page
from .url_validator import validate_url

logger = logging.getLogger(__name__)


class UrlAlreadyExists(Exception):
    pass


class DatabaseError(Exception):
    pass


class UrlRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _get_connection(self):
        try:
            logger.debug("Подключение к БД")
            return connect(self.database_url)
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise DatabaseError(f"Ошибка подключения к БД: {e}")

    def add_url(self, url: str) -> int:
        normalized_url, error = validate_url(url)
        if error:
            logger.warning(f"Некорректный URL: {url} — {error}")
            raise ValueError(error)

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                try:
                    logger.info(f"Попытка добавить URL: {normalized_url}")
                    cur.execute("SELECT id FROM urls WHERE name = %s", 
                                (normalized_url,))
                    existing = cur.fetchone()
                    if existing:
                        logger.warning(f"URL уже существует: {normalized_url}")
                        raise UrlAlreadyExists("URL уже существует")

                    cur.execute(
                        "INSERT INTO urls (name) VALUES (%s) RETURNING id", 
                        (normalized_url,)
                        )
                    url_id = cur.fetchone()['id']
                    logger.info(
                        f"URL {normalized_url} успешно добавлен с id={url_id}"
                        )
                    conn.commit()
                    return url_id
                except UrlAlreadyExists:
                    conn.rollback()
                    logger.info(
                        f"Добавление дубликата прервано: {normalized_url}"
                        )
                    raise
                except Exception as e:
                    logger.error(f"Ошибка добавления URL: {e}")
                    conn.rollback()
                    raise DatabaseError(f"Ошибка добавления URL: {e}")

    def get_url_by_id(self, url_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                logger.debug(f"Получение URL с id={url_id}")
                cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
                url = cur.fetchone()
                if url:
                    logger.info(f"URL с id={url_id} найден")
                else:
                    logger.warning(f"URL с id={url_id} не найден")
                return url

    def get_all_urls(self) -> List[dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                logger.debug("Получение списка всех URL")
                cur.execute("""
                    SELECT 
                        u.id, 
                        u.name, 
                        DATE(u.created_at) AS created_at,
                        (SELECT MAX(c.created_at) 
                            FROM url_checks c 
                            WHERE c.url_id = u.id),
                        (SELECT c.status_code 
                            FROM url_checks c 
                            WHERE c.url_id = u.id 
                            ORDER BY c.created_at DESC LIMIT 1)
                    FROM urls u
                    ORDER BY u.created_at DESC
                """)
                urls = cur.fetchall()
                logger.info(f"Получено {len(urls)} URL")
                return urls

    def create_check(self, url_id: int) -> bool:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                try:
                    logger.info(f"Проверка URL с id={url_id}")
                    cur.execute(
                        "SELECT name FROM urls WHERE id = %s", (url_id,)
                        )
                    url_record = cur.fetchone()
                    if not url_record:
                        logger.warning(f"URL с id={url_id} не найден")
                        return False

                    url = url_record['name']
                    logger.debug(f"Запрашиваем: {url}")
                    response = requests.get(url, timeout=10, verify=True)
                    response.raise_for_status()

                    # pars
                    logger.debug(f"Парсинг HTML: {url}")
                    parsed_data = parse_page(
                        response.text, url, encoding=response.encoding
                        )
                    h1 = parsed_data['h1']
                    title = parsed_data['title']
                    description = parsed_data['description']
                    status_code = response.status_code

                    cur.execute("""
                        INSERT INTO url_checks (
                                url_id, status_code, h1, title, description
                                )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (url_id, status_code, h1, title, description))
                    logger.info(
                        f"Проверка для URL id={url_id} выполнена успешно"
                        )
                    conn.commit()
                    return True
                except requests.RequestException as e:
                    logger.error(
                        f"Сетевая ошибка при проверке URL id={url_id}: {e}"
                        )
                    raise DatabaseError(f"Ошибка запроса к сайту: {e}")
                except Exception as e:
                    logger.error(
                        f"Неизвестная ошибка при проверке URL id={url_id}: {e}"
                        )
                    conn.rollback()
                    return False

    def get_checks_by_url_id(self, url_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                logger.debug(f"Получение проверок для URL id={url_id}")
                cur.execute("""
                    SELECT 
                            id, 
                            status_code, 
                            h1, title, 
                            description, 
                            DATE(created_at) AS created_at
                    FROM url_checks 
                    WHERE url_id = %s 
                    ORDER BY created_at DESC
                """, (url_id,))
                checks = cur.fetchall()
                logger.info(
                    f"Получено {len(checks)} проверок для URL id={url_id}"
                    )
                return checks