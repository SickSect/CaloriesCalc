import json
import os.path

from log.log_writer import log

product_lists = []
product_classes_idx = {}
food_mapping = {}

def get_json_config(param):
    json_path = os.path.join(os.path.dirname(__file__), 'products.json')
    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config[param]

def fill_list_on_init():
    ru_list = get_json_config('products_ru')
    en_list = get_json_config('products_en')
    for ru, eng in zip(ru_list, en_list):
        food_mapping[eng] = ru
    tmp = 0
    for product in ru_list:
        product_classes_idx[product] = tmp
        tmp += 1
    for product in ru_list:
        product_lists.append(product)
    log('info',f"Проинициализированы необходимые словари и списки для работы:\nproduct_lists: {product_lists} \nproduct_classes_idx:{product_classes_idx}\nfood_mapping:{food_mapping}")

class DataLoader:
    def __init__(self, limit):
        json_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        ru_list = config['products_ru']
        en_list = config['products_en']
        for ru, eng in zip(ru_list, en_list):
            food_mapping[eng] = ru
        self.ru_list = ru_list
        self.en_list = en_list
        # Проверить что файлы уже возможно существуют в папках
        images_folder_path = os.path.join(os.path.dirname(__file__), "downloaded_images")
        self.absent_list = {}
        for product in ru_list:
            if os.path.exists(os.path.join(images_folder_path, product)):
                product_dir_path = os.path.join(images_folder_path, product)
                num_files = len(os.listdir(product_dir_path))
                if num_files == 0:
                    log('debug',f"В папке нет файлов по классу {product}")
                    self.absent_list[product] = limit
                elif num_files < limit:
                    log('debug',f"В папке не хватает {limit - num_files} файлов по классу {product}")
                    self.absent_list[product] = limit - num_files
                log('debug',f"В папке кол-во данных соответствует необходимому лимиту по классу {product}")
            else:
                log('debug',f"В папке нет файлов по классу {product}")
                self.absent_list[product] = limit
