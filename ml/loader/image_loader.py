import os
import threading

import downloader
from PIL import Image

from log.log_writer import log
from ml.loader.data_loader import product_lists



lock = threading.Lock()
keys = product_lists
num_threads = 1
train_images_folder = ''
test_images_folder = ''

def download_train_data_for_classes(limit, folder_name):
    threads = []
    log('info',f"Количество доступных ядер / 2: {num_threads}")
    for _ in range(num_threads):
        t = threading.Thread(target=multithread_downloading, args=(limit, folder_name))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def validate_images_by_folder(folder_name):
    log('info', f'Начинаем валидацию изображений по ключам {keys}...')
    num_deleted = 0
    num_success = 0
    for key in keys:
        log('info', f'Проверка файлов по ключу: {key}')
        for root, _, files in os.walk(os.path.join(folder_name, key)):
            for file in files:
                path = os.path.join(root, file)
                try:
                    with Image.open(path) as img:
                        img.verify()
                    log('debug', f'Файл проверен: {path} его режим цвета {img.mode}')
                    num_success += 1
                except Exception as e:
                    log('error', f'❌ Битый файл: {path} {e}')
                    os.remove(path)
                    num_deleted += 1
    log('info', f'Проверка завершена!\n Удалено файлов{num_deleted}, успешно проверенных файлов {num_success}')

def multithread_downloading(limit, folder_name):
    log('debug',f"В работе поток  ----->{threading.get_ident()}")
    while True:
        lock.acquire()
        if not keys:
            lock.release()
            break
        key = keys.pop()
        lock.release()
        downloader.download(
            key,
            limit=limit,
            output_dir=folder_name,
            force_replace=False,
            adult_filter_off=False,
            timeout=10,
            verbose=False
        )
        log('debug',f"✅ Скачивание завершено! Изображения сохранены в папке: {folder_name}/{key} в потоке {threading.get_ident()}")


def multithread_absent_downloading(absent_dict, absent_keys, images_folder):
    log('debug',f"В работе поток  ----->{threading.get_ident()}")
    while True:
        lock.acquire()
        if not absent_keys:
            lock.release()
            break
        key = absent_keys.pop()
        lock.release()
        downloader.download(
            key,
            limit=absent_dict[key],
            output_dir=images_folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10,
            verbose=False
        )
        log('debug',f"✅ Скачивание завершено! Изображения сохранены в папке: {images_folder}/{key} в потоке {threading.get_ident()}")

def download_absent_data_for_classes(absent_dict, folder_name):
    log('info',f"Количество доступных ядер / 2: {num_threads}")
    new_files_dict = {}
    absent_keys = list(absent_dict.keys())
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=multithread_absent_downloading, args=(absent_dict, absent_keys, folder_name))
        t.start()
        threads.append(t)

    folder = os.path.join(os.path.dirname(__file__), folder_name)
    for product, amount in absent_dict.items():
        downloader.download(
            product,
            limit=amount,
            output_dir=folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10
        )
        log('debug',f"✅ Данные были обновлены! Изображения сохранены в папке: {folder_name}/{product}")
        for i in range(amount):
            new_files_dict[product] = f"Image_{i}"
    return new_files_dict