import io
import sqlite3
import os
import shutil
from datetime import datetime


from PIL import Image
import numpy as np

class DataCollector:
    def __init__(self):
        # сохраняем пути
        self.ml_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.ml_dir, "food_dataset.db")
        self.images_dir = os.path.join(self.ml_dir, "collected_images")

        # Создаём папки
        os.makedirs(self.images_dir, exist_ok=True)
        # Подключаем базу
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
        print(f"📊 Сборщик данных инициализирован")
        print(f"📁 Папка изображений: {self.images_dir}")
        print(f"📁 База данных: {self.db_path}")

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
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT,
                accuracy REAL,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                samples_count INTEGER
            )
        ''')
        self.conn.commit()

    def save_food_image(self, image_bytes, desc, user_id, predicted_class=None, confidence=0):
        """Сохраняет фото еды в датасет, конвертируя в JPG если нужно"""
        # Уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{user_id}.jpg"  # Всегда сохраняем как JPG
        image_path = os.path.join(self.images_dir, filename)

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

            # Сохраняем как JPG
            image.save(image_path, 'JPEG', quality=85)
            print(f"✅ Изображение сохранено как JPG: {filename}, размер: {image.size}")

        except Exception as e:
            print(f"❌ Ошибка обработки изображения: {e}")
            # Пробуем сохранить как есть
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            print(f"⚠ Сохранено как оригинал: {filename}")

        # Определяем продукт из описания
        specific_food = self.extract_specific_food(desc)

        # Сохраняем в базу
        self.conn.execute('''
                    INSERT INTO food_images 
                    (image_path, user_description, specific_food, user_id) 
                    VALUES (?, ?, ?, ?)
                ''', (image_path, desc, specific_food, user_id))
        self.conn.commit()

        print(f"✅ Данные сохранены: {filename} -> {specific_food}")
        return filename, specific_food

    def _predict_class_from_text(self, description):
        """Простая эвристика для определения класса из текста"""
        description_lower = description.lower()

        # Простые правила - потом заменим на ML модель
        if any(word in description_lower for word in ['фрукт', 'яблоко', 'банан', 'апельсин', 'груш']):
            return 'фрукты'
        elif any(word in description_lower for word in ['овощ', 'салат', 'морков', 'помидор', 'огур']):
            return 'овощи'
        elif any(word in description_lower for word in ['мясо', 'куриц', 'говядин', 'свинин', 'рыба']):
            return 'мясо_рыба'
        elif any(word in description_lower for word in ['выпечка', 'хлеб', 'булка', 'пирог', 'торт']):
            return 'выпечка'
        elif any(word in description_lower for word in ['суп', 'борщ', 'щи', 'бульон']):
            return 'супы'
        else:
            return 'другое'

    def get_labeled_data(self, min_confidence=0.6):
        """Возвращает размеченные данные для обучения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT image_path, predicted_class 
            FROM food_images 
            WHERE verified = TRUE OR confidence >= ?
        ''', (min_confidence,))

        return cursor.fetchall()

    def get_stats(self):
        """Статистика датасета"""
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