import os
import threading

from bing_image_downloader import downloader

from log.log_writer import log
from ml.data_loader import product_lists


images_folder = os.path.join(os.path.dirname(__file__), "downloaded_images")
lock = threading.Lock()
keys = product_lists
num_threads = os.cpu_count() // 2

def download_train_data_for_classes(limit):
    threads = []
    log('info',f"Количество доступных ядер / 2: {num_threads}")
    for _ in range(num_threads):
        t = threading.Thread(target=multithread_downloading, args=(limit))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def multithread_downloading(limit):
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
            output_dir=images_folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10,
            verbose=False
        )
        log('debug',f"✅ Скачивание завершено! Изображения сохранены в папке: {images_folder}/{key} в потоке {threading.get_ident()}")


def multithread_absent_downloading(absent_dict, absent_keys):
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

def download_absent_data_for_classes(absent_dict):
    log('info',f"Количество доступных ядер / 2: {num_threads}")
    new_files_dict = {}
    absent_keys = list(absent_dict.keys())
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=multithread_absent_downloading, args=(absent_dict, absent_keys))
        t.start()
        threads.append(t)


    for product, amount in absent_dict.items():
        downloader.download(
            product,
            limit=amount,
            output_dir=images_folder,
            force_replace=False,
            adult_filter_off=False,
            timeout=10
        )
        log('debug',f"✅ Данные были обновлены! Изображения сохранены в папке: {images_folder}/{product}")
        for i in range(amount):
            new_files_dict[product] = f"Image_{i}"
    return new_files_dict