import datetime
import sqlite3
import uuid

from bot.str_utils import get_lemma_word
from log.log_writer import log
from ml.data_loader import get_json_config


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
                        date TIMESTAMP NOT NULL DEFAULT NOW
                    )
            ''')
            # Заполнение таблицы products
            self.init_products_table()
            conn.commit()

    def init_products_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn = conn.cursor()
            conn.execute("SELECT COUNT(*) FROM products")
            row = conn.fetchall()
            log('info', f'Проверка необходимости инициализации таблицы products...')
            ccal_list = get_json_config('products_calories_per_hundred')
            if row == 0:
                for product in ccal_list:
                    conn.execute("INSERT INTO products VALUES (?, ?, ?)", (str(uuid.uuid4()), product['calories_per_hundred'], product['product']))
            if row != 0:
                for product in ccal_list:
                    conn.execute("SELECT product_name FROM products WHERE product_name = ?", (product['product'],))
                    row = conn.fetchone()
                    if row is None:
                        conn.execute("INSERT INTO products VALUES (?, ?, ?)", (str(uuid.uuid4()), product['calories_per_hundred'], product['product']))


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
            cursor.execute("SELECT * FROM calories_config WHERE telegram_id=$1", [telegram_id])
            row = cursor.fetchone()
            conn.commit()
            if row:
                return True
            return False

    def check_product_exists(self, product_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_name=$1", [product_name])
            row = cursor.fetchone()
            conn.commit()
            if row:
                return True
            return False

    def get_product_info(self, product_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_name=$1", [product_name])
            row = cursor.fetchone()
            conn.commit()
            return row

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

    def get_daily_limit(self, telegram_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT daily_calories FROM calories_config WHERE telegram_id = ?', [telegram_id])
            row = cursor.fetchone()
            print(row)
            if row[0] == 0:
                return None
            else:
                return row[0]

    def set_daily_calories(self, telegram_id, daily_calories):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            result = cursor.execute("UPDATE calories_config SET daily_calories = $1 where telegram_id=$2", [daily_calories, telegram_id])
            conn.commit()

    def add_product(self, product_name: str, calories_per_hundred: int):
        lemma_product_name = get_lemma_word(product_name)
        if not self.check_product_exists(lemma_product_name):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (id, "
                               "calories_per_hundread, "
                               "product_name) VALUES (?,?,?)", (str(uuid.uuid4()), calories_per_hundred, lemma_product_name))
                conn.commit()
                return True
        else:
            return False


    def get_through_lemma_calories_product(self, product_name):
        lemma_product_name = get_lemma_word(product_name)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT calories_per_hundread FROM products WHERE product_name=?", (product_name,))
            result = cursor.fetchone()
        return result

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
                log('info', f"Save new note: {[old_calories + today_calories, product_name, order_id + 1, telegram_id, current_date]}")
                result = cursor.execute("INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                                        (user_uuid, telegram_id, old_calories + today_calories, product_name, order_id + 1, current_date))
            else:
                user_uuid = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO user_calories_history (id, telegram_id, todays_calories, product_name, order_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_uuid, telegram_id, today_calories, product_name, 1, current_date))
            conn.commit()