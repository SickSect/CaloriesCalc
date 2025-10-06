import datetime
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
                        CREATE TABLE IF NOT EXISTS products (
                        id TEXT PRIMARY KEY NOT NULL,
                        calories_per_hundread INTEGER NOT NULL,
                        product_name TEXT NOT NULL
                    )
            ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_calories_history (
                        id TEXT PRIMARY KEY NOT NULL,
                        telegram_id INTEGER NOT NULL,
                        todays_calories INTEGER DEFAULT 0,
                        product_name TEXT NOT NULL,
                        order_id INTEGER NOT NULL,
                        date TIMESTAMP NOT NULL DEFAULT NOW
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

    def get_today_calories(self, telegram_id):
        current_date = datetime.date.today()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT todays_calories, product_name FROM user_calories_history WHERE telegram_id=$1 and date=$2", (telegram_id, current_date))
            rows = cursor.fetchall()
            report = []
            if rows:
                for row in rows:
                    report.append([row[1], row[0]])
                return report
            else:
                return None



    def set_daily_calories(self, telegram_id, daily_calories):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            result = cursor.execute("UPDATE calories_config SET daily_calories = $1 where telegram_id=$2", [daily_calories, telegram_id])
            conn.commit()

    def add_product(self, product_name: str, calories_per_hundread: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (id, calories_per_hundread, product_name) VALUES (?,?,?)", (str(uuid.uuid4()), calories_per_hundread, product_name))
            conn.commit()

    def get_products_info(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, calories_per_hundread FROM products")
            result = cursor.fetchall()
            product_list = []
            for row in result:
                product_list.append([row[0], row[1]])
            return product_list


    def add_calories_for_today(self, telegram_id, today_calories, product_name):
        current_date = datetime.date.today()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT todays_calories, order_id FROM user_calories_history WHERE telegram_id=$1 AND date=$2", [telegram_id,current_date])
            row = cursor.fetchone()
            if row:
                user_uuid = str(uuid.uuid4())
                old_calories = row[0]
                order_id = row[1]
                print("Save new note:", [old_calories + today_calories, product_name, order_id + 1, telegram_id, current_date])
                result = cursor.execute("INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                                        (user_uuid, telegram_id, old_calories + today_calories, product_name, order_id + 1, current_date))
            else:
                user_uuid = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_uuid, telegram_id, today_calories, product_name, 1, current_date))
            conn.commit()