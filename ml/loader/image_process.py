import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import PIL
from icrawler.builtin import BingImageCrawler

from log.log_writer import log
from ml.loader.data_loader import product_lists, get_json_config

keys = product_lists

def download_product(product, amount, folder, limit):
    try:
        product_folder = os.path.join(folder, product)
        log('info', f'DOWNLOADING for folder: {product_folder} amount: {amount} and product: {product}')
        os.makedirs(product_folder, exist_ok=True)
        crawler = BingImageCrawler(
            storage={'root_dir': product_folder},
            log_level='INFO'
        )
        crawler.crawl(
            keyword=product,
            max_num=amount,
            min_size=(500, 500),
            max_size=(1920, 1080),
            file_idx_offset=limit - amount + 1
        )
        return f"✅ {product}: {amount} изображений"
    except Exception as e:
        return f"❌ {product}: ошибка - {str(e)}"

def download_data_to_folder(absent_dict, folder_name, max_workers=4):
    """
        Скачивает изображения для всех продуктов параллельно

        Args:
            product_dict: dict {product_name: count}
            base_folder: папка для сохранения
            max_workers: сколько продуктов качать одновременно (4-6 оптимально)
        """
    root_dir = os.path.dirname(__file__)
    root_dir = os.path.join(root_dir, folder_name)
    os.makedirs(root_dir, exist_ok=True)
    limit = 0
    if folder_name == 'test_images':
        limit = get_json_config("test_product_limit")
    if folder_name == 'train_images':
        limit = get_json_config("train_product_limit")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи
        future_to_product = {
            executor.submit(download_product, product, amount, root_dir, limit): product
            for product, amount in absent_dict.items()
        }

        # Собираем результаты
        for future in as_completed(future_to_product):
            result = future.result()
            print('RESULT: ', result)

def save_image_to_db_by_folder(folder_name, collector):
    root_path = os.path.join(os.path.dirname(__file__), folder_name)
    files = []
    print("Тип Image:", type(Image))  # Должно быть: <class 'type'>
    # Собираем внутри папки все файлы
    log('info', f'Start saving images in {folder_name}')
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            log('info', f'SAVING image {item_path}')
            for filename in os.listdir(item_path):
                file_path = os.path.join(item_path, filename)
                log('debug', f'file_path: {file_path}')
                if os.path.isfile(file_path):
                    try:
                        with PIL.Image.open(file_path) as img:
                            img.verify()
                    except Exception as e:
                        log('info', f"❌ Пропущено изображение {file_path}: {e}")
                        continue  # пропускаем битые файлы
                    collector.save_food_image_by_path(folder_name=='train_images', file_path, 'system_image_adding', 0, item)
                    files.append(file_path)

