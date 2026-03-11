import datetime
import sqlite3
import uuid
from typing import Optional, List, Dict, Any, Tuple

from log.log_writer import log
from ml.data_loader import get_json_config


class Database:
    """Управление базой данных бота"""

    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с БД (для удобного мокирования в тестах)"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Инициализация таблиц"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calories_config (
                    id TEXT PRIMARY KEY NOT NULL,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    daily_calories INTEGER DEFAULT 0,
                    products TEXT DEFAULT '{}'
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY NOT NULL,
                    calories_per_hundred INTEGER NOT NULL,
                    product_name TEXT NOT NULL UNIQUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_calories_history (
                    id TEXT PRIMARY KEY NOT NULL,
                    telegram_id INTEGER NOT NULL,
                    todays_calories INTEGER DEFAULT 0,
                    product_name TEXT NOT NULL,
                    order_id INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self._init_products_table(cursor)
            conn.commit()

    def _init_products_table(self, cursor: sqlite3.Cursor):
        """Заполнение таблицы продуктами"""
        cursor.execute("SELECT COUNT(*) FROM products")
        row = cursor.fetchone()
        log('info', 'Проверка необходимости инициализации таблицы products...')

        ccal_list = get_json_config('products_calories_per_hundred')

        if row[0] == 0:
            for product in ccal_list:
                cursor.execute(
                    "INSERT INTO products (id, calories_per_hundred, product_name) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), product['calories_per_hundred'], product['product'])
                )
        else:
            for product in ccal_list:
                cursor.execute("SELECT product_name FROM products WHERE product_name = ?", (product['product'],))
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO products (id, calories_per_hundred, product_name) VALUES (?, ?, ?)",
                        (str(uuid.uuid4()), product['calories_per_hundred'], product['product'])
                    )

    def check_user_exists(self, telegram_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM calories_config WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone() is not None

    def add_user(self, telegram_id: int) -> str:
        """Добавляет пользователя, возвращает UUID"""
        user_uuid = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO calories_config (id, telegram_id, daily_calories, products) VALUES (?, ?, ?, ?)",
                (user_uuid, telegram_id, 0, '{}')
            )
            conn.commit()
        return user_uuid

    def set_daily_calories(self, telegram_id: int, daily_calories: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE calories_config SET daily_calories = ? WHERE telegram_id = ?",
                (daily_calories, telegram_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_daily_limit(self, telegram_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT daily_calories FROM calories_config WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            return row[0] if row and row[0] > 0 else None

    def check_product_exists(self, product_name: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM products WHERE product_name = ?", (product_name,))
            return cursor.fetchone() is not None

    def get_product_info(self, product_name: str) -> Optional[Tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, calories_per_hundred, product_name FROM products WHERE product_name = ?",
                           (product_name,))
            return cursor.fetchone()

    def add_product(self, product_name: str, calories_per_hundred: int) -> bool:
        """Добавляет продукт, возвращает True если успешно"""
        if self.check_product_exists(product_name):
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (id, calories_per_hundred, product_name) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), calories_per_hundred, product_name)
            )
            conn.commit()
            return True

    def get_today_calories(self, telegram_id: int) -> Optional[List[List]]:
        """Возвращает список [продукт, калории] за сегодня"""
        current_date = datetime.date.today()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_name, todays_calories FROM user_calories_history WHERE telegram_id = ? AND date = ?",
                (telegram_id, current_date)
            )
            rows = cursor.fetchall()
            return [[row[0], row[1]] for row in rows] if rows else None

    def add_calories_for_today(self, telegram_id: int, calories: float, product_name: str):
        """Добавляет запись о калориях за сегодня"""
        current_date = datetime.date.today()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT todays_calories, order_id FROM user_calories_history WHERE telegram_id = ? AND date = ?",
                (telegram_id, current_date)
            )
            row = cursor.fetchone()

            user_uuid = str(uuid.uuid4())

            if row:
                old_calories = row[0]
                order_id = row[1]
                cursor.execute(
                    "INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_uuid, telegram_id, old_calories + calories, product_name, order_id + 1, current_date)
                )
            else:
                cursor.execute(
                    "INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_uuid, telegram_id, calories, product_name, 1, current_date)
                )

            conn.commit()

    def get_products_info(self) -> List[List]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, calories_per_hundred FROM products")
            return [[row[0], row[1]] for row in cursor.fetchall()]