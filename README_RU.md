# FoodCalorieBot — Telegram-бот для учёта калорий и распознавания продуктов

FoodCalorieBot — это Telegram-бот, который:
* устанавливает дневной лимит калорий
* считает калории
* показывает статистику
* хранит продукты
* распознаёт продукты по фото
* автоматически собирает датасет
* обучает ML-модель (в процессе реализации)

```
📂 Структура проекта
project/
 ┣ bot/
 ┃ ┣ db.py
 ┃ ┣ str_utils.py
 ┃ ┗ ...
 ┣ ml/
 ┃ ┣ food_model.py
 ┃ ┣ dataset_init.py
 ┃ ┣ dataset_collector.py
 ┃ ┣ data_loader.py
 ┃ ┣ image_loader.py
 ┃ ┗ trained_model.pth
 ┣ log/
 ┃ ┗ log_writer.py
 ┣ products.json
 ┣ main.py
 ┣ requirements.txt
 ┗ README.md
```

# 🔧 Установка и запуск
## 1. Клонирование репозитория
git clone https://github.com/your/repo.git
cd repo

## 2. Установка зависимостей
pip install -r requirements.txt

## 3. Создание файла .env

Создайте файл:

BOT_TOKEN=ВАШ_ТОКЕН

## 4. Запуск бота
python main.py

# 📘 Файл products.json

Содержит описание классов продуктов и их калорийность.

```
{
  "product_limit": 50,
  "products_ru": ["яблоко", "картофель"],
  "products_en": ["apple", "potato"],
   {"product": "яблоко", "calories_per_hundred": 52},
    {"product": "банан", "calories_per_hundred": 89},
}
```

# 🤖 Возможности бота
## ⭐ Установка дневного лимита

Сохраняет лимит, уведомляет о превышении.

## ➕ Добавление калорий

Можно указать вес продукта, бот сам высчитает калории.

## 📊 Калории за сегодня

Показывает:
текущий лимит
сколько уже съедено
список продуктов за день
## 📚 Добавление новых продуктов

Добавляет в SQLite названия и калорийность.

## 🖼 Распознавание еды по фото

Бот:

принимает фото
предсказывает продукт
показывает процент уверенности

Веса хранятся в ml/trained_model.pth.

# 🗄 Работа с датасетом
При первом запуске:

* бот проверяет наличие датасета
* при отсутствии — скачивает нужное количество картинок
* создаёт SQLite-базу
* валидирует изображения на наличие брака
* обучение можно запустить при достаточном количестве изображений
* дата сет заполняется в фоновом процессе
* обучение идет также в фоновом процессе

# 🛠 Используемые технологии

* python-telegram-bot 20+
* PyTorch
* SQLite
* Pillow
* requests
* python-dotenv

| Библиотека / Импорт | Лицензия и ссылка |
| ------------------ |:----------------:|
| python-dotenv (`from dotenv import load_dotenv`) | MIT — [github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) |
| python-telegram-bot (`from telegram import Update, ...` / `from telegram.ext import ...`) | LGPLv3 — [github.com/python-telegram-bot/python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) |
| NumPy (`import numpy as np`) | BSD — [github.com/numpy/numpy](https://github.com/numpy/numpy) |
| PyTorch (`import torch`, `import torch.nn as nn`, `from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler`) | BSD-style — [github.com/pytorch/pytorch](https://github.com/pytorch/pytorch) |
| Torchvision (`import torchvision.transforms as transforms`, `import torchvision.models as models`) | BSD-style — [github.com/pytorch/vision](https://github.com/pytorch/vision) |
| Pillow (PIL) (`from PIL import Image, ImageFile, UnidentifiedImageError`) | PIL Software License (MIT-like) — [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |

