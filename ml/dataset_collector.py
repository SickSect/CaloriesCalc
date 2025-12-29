import io
import sqlite3
import os
from datetime import datetime

from PIL import Image

from log.log_writer import log
from ml.loader.data_loader import product_lists


class DataCollector:
    def __init__(self):
        # сохраняем пути
        self.ml_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.ml_dir, "food_dataset.db")
        self.images_dir = os.path.join(self.ml_dir, "collected_images")

        # Список конкретных продуктов (будем расширять)
        self.specific_foods = product_lists
        # Создаём папки
        os.makedirs(self.images_dir, exist_ok=True)
        # Подключаем базу
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
        log('debug',f"📊 Сборщик данных инициализирован")
        log('debug',f"📁 Папка изображений: {self.images_dir}")
        log('debug',f"📁 База данных: {self.db_path}")

    def extract_specific_food(self, description):
        """Извлекает конкретный продукт из описания пользователя"""
        description_lower = description.lower()

        # Ищем точные совпадения с нашим списком продуктов
        for food in self.specific_foods:
            if food in description_lower:
                return food

        # Если точного совпадения нет, ищем по корням слов
        import re
        words = re.findall(r'\b[а-я]+\b', description_lower)
        for word in words:
            for food in self.specific_foods:
                if food.startswith(word[:3]) and len(word) >= 3:  # Совпадение по первым 3 буквам
                    return food

        return "неизвестно"

    def create_tables(self):
        """Создаёт таблицы для датасета"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS food_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                user_description TEXT,
                predicted_class TEXT,
                confidence REAL,
                verified BOOLEAN DEFAULT FALSE,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS test_food_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_path TEXT NOT NULL,
                        user_description TEXT,
                        predicted_class TEXT,
                        confidence REAL,
                        verified BOOLEAN DEFAULT FALSE,
                        user_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT,
                accuracy REAL,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                samples_count INTEGER
            )
        ''')
        self.conn.commit()

    def save_food_image(self, train_flag, path, image_bytes, desc, user_id, predicted_class=None, confidence=0):
        self.conn = sqlite3.connect(self.db_path)
        """Сохраняет фото еды в датасет, конвертируя в JPG если нужно"""
        image_path = os.path.join(self.images_dir, path)
        try:
            # Открываем изображение с помощью PIL (поддерживает PNG, JPG, etc.)
            image = Image.open(io.BytesIO(image_bytes))
            # Конвертируем в RGB если нужно (PNG может иметь альфа-канал)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Создаём белый фон для прозрачных PNG
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

        except Exception as e:
            log('error',f"❌ Ошибка обработки изображения: {e}")

        specific_food = self.extract_specific_food(desc)
        table_name = ''
        if not train_flag:
            table_name = 'test_food_images'
        else:
            table_name = 'food_images'
        # Сохраняем в базу
        self.conn.execute('''
                    INSERT INTO ''' + table_name + ''' 
                    (image_path, user_description, predicted_class, verified, user_id, created_at) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (image_path, desc, specific_food, True, user_id, datetime.now()))
        self.conn.commit()

        log('debug',f"✅ Данные сохранены: {image_path} -> {specific_food}")
        self.close()
        return specific_food

    def get_labeled_data(self, min_confidence=0.6):
        """Возвращает размеченные данные для обучения"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT image_path, predicted_class 
            FROM food_images 
            WHERE verified = TRUE OR confidence >= ?
        ''', (min_confidence,))

        return cursor.fetchall()

    def get_stats(self):
        """Статистика датасета"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Общее количество
        cursor.execute("SELECT COUNT(*) FROM food_images")
        total = cursor.fetchone()[0]

        # По классам
        cursor.execute('''
            SELECT predicted_class, COUNT(*) 
            FROM food_images 
            GROUP BY predicted_class
        ''')
        by_class = dict(cursor.fetchall())

        # Для обучения
        trainable = len(self.get_labeled_data())
        self.close()
        return {
            'total_images': total,
            'by_class': by_class,
            'trainable_samples': trainable,
            'can_train': trainable >= 20,  # Минимум 20 образцов
            'images_dir': self.images_dir
        }


    def get_training_status(self):
        """Статус для обучения"""
        stats = self.get_stats()

        status = (
            f"📊 Статистика датасета:\n"
            f"• Всего фото: {stats['total_images']}\n"
            f"• Пригодно для обучения: {stats['trainable_samples']}\n"
            f"• Можно обучать: {'✅ ДА' if stats['can_train'] else '❌ НЕТ'}\n"
        )

        if stats['by_class']:
            status += "📈 Распределение по классам:\n"
            for cls, count in stats['by_class'].items():
                status += f"  • {cls}: {count} фото\n"

        return status

    def close(self):
        self.conn.close()