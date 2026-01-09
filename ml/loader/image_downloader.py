import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from icrawler.builtin import GoogleImageCrawler

from log.log_writer import log
from ml.loader.data_loader import product_lists

keys = product_lists

def download_product(product, amount, folder):
    try:
        product_folder = os.path.join(folder, product)
        product_folder = os.path.join(os.path.dirname(__file__), product_folder)
        log('info', f'DOWNLOADING for folder: {product_folder} amount: {amount} and product: {product}')
        os.makedirs(product_folder, exist_ok=True)
        crawler = GoogleImageCrawler(
            storage={'root_dir': product_folder},
            log_level='INFO'
        )
        crawler.crawl(
            keyword=product,
            max_num=amount,
            min_size=(500, 500),
            max_size=(1920, 1080),
            file_idx_offset=0
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
    os.makedirs(folder_name, exist_ok=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи
        future_to_product = {
            executor.submit(download_product, product, amount, folder_name): product
            for product, amount in absent_dict.items()
        }

        # Собираем результаты
        for future in as_completed(future_to_product):
            result = future.result()
            print('RESULT: ', result)