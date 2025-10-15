import os
from bing_image_downloader import downloader

from ml.product_lists import product_lists

limit = 1
images_folder = os.path.join(os.path.dirname(__file__), "downloaded_images")

def download_train_data_for_classes():
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