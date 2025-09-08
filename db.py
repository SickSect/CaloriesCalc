import sqlite3
import uuid


class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Создание таблицы
            cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calories_config (
                        id TEXT PRIMARY KEY NOT NULL,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        daily_calories INTEGER DEFAULT 0,
                        products TEXT DEFAULT '{}'
                    )
                    ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_calories_history (
                        id TEXT PRIMARY KEY NOT NULL,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        todays_calories INTEGER DEFAULT 0
                    )
            ''')
            conn.commit()

    def get_user_calories_per_day(self, telegram_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calories_config WHERE telegram_id=?", (telegram_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'daily_calories': row['daily_calories'],
                    'products': row['products']
                }
            return None

    def add_user(self, telegram_id):
        user_uuid = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO calories_config (id, telegram_id, daily_calories, products) VALUES (?, ?, ?, ?)", (user_uuid, telegram_id, 0, '{}'))
            conn.commit()

    def check_user_exists(self, telegram_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calories_config WHERE telegram_id=?", (telegram_id,))
            row = cursor.fetchone()
            conn.commit()
            if row:
                return True
            return False

    def set_daily_calories(self, telegram_id, daily_calories):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            result = cursor.execute("UPDATE calories_config SET daily_calories = $1 where telegram_id=$2", [daily_calories, telegram_id])
            conn.commit()