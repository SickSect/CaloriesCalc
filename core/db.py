import asyncpg
import json
import os
import logging
from typing import Optional, List, Tuple
import datetime

logger = logging.getLogger(__name__)


def _load_json(filename: str) -> list:
    path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Database:
    """Управление базой данных через asyncpg"""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создаёт пул соединений и инициализирует схему"""
        self._pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "calories_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            min_size=1,
            max_size=5
        )
        await self._init_schema()
        logger.info("[DB] connected to PostgreSQL")

    async def disconnect(self):
        """Закрывает пул соединений"""
        if self._pool:
            await self._pool.close()
            logger.info("[DB] disconnected")

    async def _init_schema(self):
        """Применяет schema.sql"""
        schema_path = os.path.join(os.path.dirname(__file__), "sql\\schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            schema = f.read()
        async with self._pool.acquire() as conn:
            await conn.execute(schema)
        await self._init_products()

    async def _init_products(self):
        """Заполняет таблицу products из JSON если она пустая"""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM products")
            if count > 0:
                return

            products = _load_json("products.json")
            await conn.executemany(
                "INSERT INTO products (product_name, calories_per_hundred) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                [(p["product"], p["calories_per_hundred"]) for p in products]
            )
            logger.info(f"[DB] inserted {len(products)} products")

    # ──────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────

    async def check_user_exists(self, telegram_id: int) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM calories_config WHERE telegram_id = $1",
                telegram_id
            )
            return row is not None

    async def add_user(self, telegram_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO calories_config (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING",
                telegram_id
            )

    async def set_daily_calories(self, telegram_id: int, daily_calories: int) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE calories_config SET daily_calories = $1 WHERE telegram_id = $2",
                daily_calories, telegram_id
            )
            return result == "UPDATE 1"

    async def get_daily_limit(self, telegram_id: int) -> Optional[int]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT daily_calories FROM calories_config WHERE telegram_id = $1",
                telegram_id
            )
            return row["daily_calories"] if row and row["daily_calories"] > 0 else None

    # ──────────────────────────────────────────
    # Products
    # ──────────────────────────────────────────

    async def check_product_exists(self, product_name: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM products WHERE product_name = $1",
                product_name
            )
            return row is not None

    async def get_product_info(self, product_name: str) -> Optional[Tuple]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, calories_per_hundred, product_name FROM products WHERE product_name = $1",
                product_name
            )
            return (str(row["id"]), row["calories_per_hundred"], row["product_name"]) if row else None

    async def add_product(self, product_name: str, calories_per_hundred: int) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "INSERT INTO products (product_name, calories_per_hundred) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                product_name, calories_per_hundred
            )
            return result == "INSERT 0 1"

    async def get_products_info(self) -> List[List]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT product_name, calories_per_hundred FROM products")
            return [[row["product_name"], row["calories_per_hundred"]] for row in rows]

    # ──────────────────────────────────────────
    # Calories history
    # ──────────────────────────────────────────

    async def get_today_calories(self, telegram_id: int) -> Optional[List[List]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT product_name, calories
                   FROM user_calories_history
                   WHERE telegram_id = $1 AND date = CURRENT_DATE
                   ORDER BY order_id""",
                telegram_id
            )
            return [[row["product_name"], float(row["calories"])] for row in rows] if rows else None

    async def add_calories_for_today(self, telegram_id: int, calories: float, product_name: str):
        async with self._pool.acquire() as conn:
            # Считаем текущий максимальный order_id за сегодня
            max_order = await conn.fetchval(
                """SELECT COALESCE(MAX(order_id), 0)
                   FROM user_calories_history
                   WHERE telegram_id = $1 AND date = CURRENT_DATE""",
                telegram_id
            )
            await conn.execute(
                """INSERT INTO user_calories_history
                   (telegram_id, calories, product_name, order_id, date)
                   VALUES ($1, $2, $3, $4, CURRENT_DATE)""",
                telegram_id, calories, product_name, max_order + 1
            )