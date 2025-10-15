product_lists = [
            'апельсин',
            'болгарский перец',
            'говядина',
            'гречка',
            'котлета',
            'курица',
            'лимон',
            'макароны',
            'огурец',
            'помидор',
            'пюре',
            'салат',
            'тыква',
            'хлеб белый',
            'хлеб черный'
]

product_classes_idx = {
            'апельсин' : 0,
            'болгарский перец' : 1,
            'говядина' : 2,
            'гречка' : 3,
            'котлета' : 4,
            'курица' : 5,
            'лимон' : 6,
            'макароны' : 7,
            'огурец' : 8,
            'помидор' : 9,
            'пюре' : 10,
            'салат' : 11,
            'тыква' : 12,
            'хлеб белый' : 13,
            'хлеб черный' : 14
}

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

def fill_list_on_init(ru_list, eng_list):
    for ru, eng in ru_list.items(), eng_list.items():
        food_mapping[eng] = ru
    tmp = 0
    for product in ru_list:
        product_classes_idx[product] = tmp
        tmp += 1
    for product in ru_list:
        product_lists.append(product)