import os
from bing_image_downloader import downloader

from ml.product_lists import product_lists


images_folder = os.path.join(os.path.dirname(__file__), "downloaded_images")

def download_train_data_for_classes(limit):
    for product in product_lists:
        downloader.download(
            product,
            limit=limit,
            output_dir=images_folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10
        )
        print(f"✅ Скачивание завершено! Изображения сохранены в папке: {images_folder}/{product}")

def download_absent_data_for_classes(absent_dict, limit):
    for product, amount in absent_dict.items():
        downloader.download(
            product,
            limit=amount,
            output_dir=images_folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10
        )
        print(f"✅ Данные были обновлены! Изображения сохранены в папке: {images_folder}/{product}")