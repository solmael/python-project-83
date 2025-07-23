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
            raise ValueError(error)

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                try:
                    cur.execute(
                        "SELECT id FROM urls WHERE name = %s", (normalized_url,)
                        )
                    existing = cur.fetchone()
                    if existing:
                        raise UrlAlreadyExists("Страница уже существует")

                    cur.execute(
                        "INSERT INTO urls (name) "
                        "VALUES (%s) RETURNING id", 
                        (normalized_url,)
                        )
                    url_id = cur.fetchone()['id']
                    conn.commit()
                    return url_id
                except UrlAlreadyExists:
                    conn.rollback()
                    raise
                except Exception as e:
                    conn.rollback()
                    raise DatabaseError(f"Ошибка добавления URL: {e}")

    def get_url_by_id(self, url_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
                return cur.fetchone()
    
    def get_url_by_name(self, name: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id, name FROM urls WHERE name = %s", (name,))
                result = cur.fetchone()
                return result

    def get_all_urls(self) -> List[dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
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
                return cur.fetchall()

    def create_check(self, url_id: int) -> bool:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                url_record = cur.fetchone()
                if not url_record:
                    return False

                url = url_record['name']
                try:
                    response = requests.get(url, timeout=10, verify=True)
                    status_code = response.status_code

                    if 200 <= status_code < 300:
                        parsed_data = parse_page(response.text, url, encoding=response.encoding)
                    else:
                        parsed_data = {
                            'h1': None,
                            'title': None,
                            'description': None
                        }
                except requests.RequestException as e:
                    status_code = 0
                    parsed_data = {
                        'h1': None,
                        'title': None,
                        'description': None
                    }

                h1 = parsed_data['h1']
                title = parsed_data['title']
                description = parsed_data['description']

                cur.execute("""
                    INSERT INTO url_checks (url_id, status_code, h1, title, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (url_id, status_code, h1, title, description))
                conn.commit()
                return True
                
    def get_last_check_status(self, url_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT status_code FROM url_checks WHERE url_id = %s ORDER BY created_at DESC LIMIT 1", (url_id,))
                result = cur.fetchone()
                return result['status_code'] if result else None

    def get_checks_by_url_id(self, url_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT id, 
                            status_code, 
                            h1, 
                            title, 
                            description, 
                            DATE(created_at) AS created_at
                    FROM url_checks 
                    WHERE url_id = %s 
                    ORDER BY created_at DESC
                """, (url_id,))
                return cur.fetchall()