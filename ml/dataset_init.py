import os
import re

food_mapping = {
        # Пример: имя_файла -> продукт
        'apple': 'яблоко',
        'banana': 'банан',
        'lemon': 'лимон',
        'orange': 'апельсин',
        'cucumber': 'огурец',
        'tomato': 'помидор',
        'carrot': 'морковь',
        'pumpkin': 'тыква',
        'puree': 'пюре',
        'cutlet': 'котлета',
        'bell pepper': 'болгарский перец',
        'potato': 'картофель',
        'onion': 'лук',
        'cabbage': 'капуста',
        'lettuce': 'салат',
        'chicken': 'курица',
        'beef': 'говядина',
        'pork': 'свинина',
        'steak': 'стейк',
        'fish': 'рыба',
        'eggs': 'яйца',
        'cheese': 'сыр',
        'milk': 'молоко',
        'yogurt': 'йогурт',
        'bread white': 'хлеб белый',
        'bread black': 'хлеб черный',
        'rice': 'рис',
        'buckwheat': 'гречка',
        'pasta': 'макароны'
    }

def init_database(collector):
    """Инициализирует базу данных и заполняет её готовыми изображениями"""
    print("🗄️ Инициализация базы данных...")
    if os.path.exists(os.path.join(os.path.dirname(__file__), "food_dataset.db")):
        print("База данных была проинициализирована!")
        return
    # Путь к папке с готовыми изображениями
    images_folder = os.path.join(os.path.dirname(__file__), "food_image")
    if not os.path.exists(images_folder):
        print(f"❌ Папка с изображениями не найдена: {images_folder}")
        print("📁 Создайте папку ml/food_images и положите туда изображения")
        return

    # Список файлов в папке
    image_files = [f for f in os.listdir(images_folder)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    if not image_files:
        print(f"❌ В папке {images_folder} нет изображений")
        print("📸 Добавьте изображения продуктов в формате JPG, PNG или BMP")
        return

    print(f"📁 Найдено {len(image_files)} изображений в папке")
    added_count = 0
    skipped_count = 0

    for filename in image_files:
        try:
            # Пытаемся определить продукт по имени файла
            file_key = os.path.splitext(filename)[0].lower()
            file_key_array = file_key.split('_')
            file_key = ''
            for word in file_key_array:
                if not re.findall(r'\d+', word):
                    file_key += word
                file_key += ' '
            file_key = file_key.lstrip()
            file_key = file_key.rstrip()

            # Ищем точное совпадение
            if file_key in food_mapping:
                food_name = food_mapping[file_key]
            else:
                # Ищем частичное совпадение
                for key, product in food_mapping.items():
                    if key in file_key:
                        food_name = product
                        break

            if not food_name:
                # Если не нашли в mapping, используем имя файла как есть
                food_name = file_key
                print(f"⚠ Неизвестный продукт для файла {filename}, используем '{food_name}'")

            # Полный путь к файлу
            file_path = os.path.join(images_folder, filename)

            # Читаем файл
            with open(file_path, 'rb') as f:
                image_bytes = f.read()

            # Сохраняем в базу данных
            saved_filename, detected_food = collector.save_food_image(
                image_bytes, food_name, user_id=0  # user_id=0 для системных записей
            )

            print(f"✅ Добавлено: {filename} -> {detected_food}")
            added_count += 1

        except Exception as e:
            print(f"❌ Ошибка при обработке {filename}: {e}")
            skipped_count += 1

    # Получаем статистику
    stats = collector.get_stats()

    print("\n📊 Результат инициализации:")
    print(f"✅ Успешно добавлено: {added_count} изображений")
    print(f"❌ Пропущено: {skipped_count} изображений")
    print(f"📈 Всего в базе: {stats['total_images']} изображений")

    # Проверяем возможность обучения
    if stats['can_train']:
        print(f"\n🎯 Можно обучать модель! Достаточно данных.")
    else:
        print(f"\n📝 Нужно больше данных для обучения.")
        print(f"   Собрано: {stats['trainable_samples']} фото")
        print(f"   Нужно: минимум 20 фото и 5 различных продуктов")

    collector.close()