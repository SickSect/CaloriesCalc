import os
import re

from log.log_writer import log
from ml.data_loader import product_lists

def add_files_to_train_database(new_files_dict, collector, train):
    for key, filename in new_files_dict.items():
        for path in filename:
            with open(path, 'rb') as f:
                image_bytes = f.read()
            # Сохраняем в базу данных

            detected_food = collector.save_food_image(
                train,
                path,
                image_bytes,
                image_bytes, key, user_id=0  # user_id=0 для системных записей
            )
            log('info',f"    ✅ Добавлено: {filename} -> {detected_food}")

def init_database(collector):
    """Инициализирует базу данных и заполняет её готовыми изображениями"""
    log('debug',"🗄️ Инициализация базы данных...")
    if os.path.exists(os.path.join(os.path.dirname(__file__), "food_dataset.db")):
        log('debug',"База данных была проинициализирована!")
    # Путь к папке с готовыми изображениями
    images_folder = os.path.join(os.path.dirname(__file__), "downloaded_images")
    if not os.path.exists(images_folder):
        log('error',f"❌ Папка с изображениями не найдена: {images_folder}")
        log('error',"📁 Создайте папку ml/downloaded_images и положите туда изображения")
        return

    image_dict = {}
    added_count = 0
    skipped_count = 0
    for key in product_lists:
        category_path = os.path.join(images_folder, key)
        # Список файлов в папке
        image_files = [f for f in os.listdir(category_path)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        # TODO надо добавить валидациб файлов было, часть битые блин!
        if not image_files:
            log('error',f"❌ В папке {images_folder} нет изображений по классу {key}")
            log('error',f"📸 Добавьте изображения продуктов в формате JPG, PNG или BMP в класс {key}")
        log('info',f"📁 Найдено {len(image_files)} изображений в папке по классу {key}")

        image_dict[key] = image_files

    for key, files in image_dict.items():
        try:
            food_name = key
            # Полный путь к файлу
            class_folder = os.path.join(images_folder, key)
            log('info',f"Читаем папку: {class_folder}")
            for file in files:
                file_path = os.path.join(class_folder, file)
                log('debug',f"читаем файл: {file}")
                # Читаем файл
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()

                # Сохраняем в базу данных
                detected_food = collector.save_food_image(
                    file_path,
                    image_bytes, food_name, user_id=0  # user_id=0 для системных записей
                )
                log('debug',f"✅ Добавлено: {file} -> {detected_food}")
                added_count += 1
        except Exception as e:
            log('error',f"❌ Ошибка при обработке {key}: {e}")
            skipped_count += 1

    # Получаем статистику
    stats = collector.get_stats()

    log('debug',"\n📊 Результат инициализации:")
    log('debug',f"✅ Успешно добавлено: {added_count} изображений")
    log('debug',f"❌ Пропущено: {skipped_count} изображений")
    log('debug',f"📈 Всего в базе: {stats['total_images']} изображений")

    # Проверяем возможность обучения
    if stats['can_train']:
        log('debug',f"\n🎯 Можно обучать модель! Достаточно данных.")
    else:
        log('debug',f"\n📝 Нужно больше данных для обучения.")
        log('debug',f"   Собрано: {stats['trainable_samples']} фото")
        log('debug',f"   Нужно: минимум 20 фото и 5 различных продуктов")

    collector.close()