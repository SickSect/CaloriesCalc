import os
import re

from ml.data_loader import product_lists

def add_files_to_database(new_files_dict, collector):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for key, filename in new_files_dict.items():
        category_dir = os.path.join(current_dir, key)
        for path in filename:
            with open(path, 'rb') as f:
                image_bytes = f.read()
            # Сохраняем в базу данных
            saved_filename, detected_food = collector.save_food_image(
                image_bytes, key, user_id=0  # user_id=0 для системных записей
            )
            print(f"    ✅ Добавлено: {saved_filename} -> {detected_food}")


def init_database(collector):
    """Инициализирует базу данных и  заполняет её готовыми изображениями"""
    print("🗄️ Инициализация базы данных...")
    if os.path.exists(os.path.join(os.path.dirname(__file__), "food_dataset.db")):
        print("База данных была проинициализирована!")
    # Путь к папке с готовыми изображениями
    images_folder = os.path.join(os.path.dirname(__file__), "downloaded_images")
    if not os.path.exists(images_folder):
        print(f"❌ Папка с изображениями не найдена: {images_folder}")
        print("📁 Создайте папку ml/downloaded_images и положите туда изображения")
        return

    image_dict = {}
    added_count = 0
    skipped_count = 0
    for key in product_lists:
        category_path = os.path.join(images_folder, key)
        # Список файлов в папке
        image_files = [f for f in os.listdir(category_path)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        if not image_files:
            print(f"❌ В папке {images_folder} нет изображений по классу {key}")
            print(f"📸 Добавьте изображения продуктов в формате JPG, PNG или BMP в класс {key}")
        print(f"📁 Найдено {len(image_files)} изображений в папке по классу {key}")

        image_dict[key] = image_files

    for key, files in image_dict.items():
        try:
            food_name = key
            # Полный путь к файлу
            class_folder = os.path.join(images_folder, key)
            print(f"Читаем папку: {class_folder}")
            for file in files:
                file_path = os.path.join(class_folder, file)
                print(f"читаем файл: {file}")
                # Читаем файл
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()

                # Сохраняем в базу данных
                saved_filename, detected_food = collector.save_food_image(
                    image_bytes, food_name, user_id=0  # user_id=0 для системных записей
                )
                print(f"    ✅ Добавлено: {file} -> {detected_food}")
                added_count += 1
        except Exception as e:
            print(f"    ❌ Ошибка при обработке {key}: {e}")
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