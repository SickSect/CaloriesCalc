# FoodCalorieBot — Telegram bot for calorie tracking and food recognition

FoodCalorieBot is a Telegram bot that:
* sets a daily calorie limit
* counts calories
* shows statistics
* stores products
* recognizes products from photos
* automatically collects a dataset
* trains an ML model (in progress)

```
📂 Project structure
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



# 🔧 Installation and launch
## 1. Clone the repository
git clone https://github.com/your/repo.git  
cd repo

## 2. Install dependencies
pip install -r requirements.txt

## 3. Create the .env file

Create a file:

BOT_TOKEN=YOUR_TOKEN

## 4. Run the bot
python main.py

# 📘 File products.json

Contains product class descriptions and their caloric values.

{
"product_limit": 50,
"products_ru": ["яблоко", "картофель"],
"products_en": ["apple", "potato"],
 {"product": "яблоко", "calories_per_hundred": 52},
    {"product": "банан", "calories_per_hundred": 89},
}

# 🤖 Bot features
## ⭐ Setting a daily calorie limit

Stores the limit and notifies if exceeded.

## ➕ Adding calories

You can specify the product weight — the bot will calculate calories automatically.

## 📊 Calories for today

Shows:  
current limit  
how much is already eaten  
list of products for today  

## 📚 Adding new products

Adds product names and calories to SQLite.

## 🖼 Food recognition from photos

The bot:

* accepts a photo  
* predicts the product  
* shows confidence percentage  

Model weights are stored in ml/trained_model.pth.

# 🗄 Dataset handling
On the first launch:

* the bot checks if a dataset exists  
* if not — downloads the required number of images  
* creates an SQLite database  
* validates images for defects  
* model training can start once enough images are collected  
* dataset is filled in a background process  
* training also runs in a background process  

# 🛠 Technologies used

* python-telegram-bot 20+  
* PyTorch  
* SQLite  
* Pillow  
* requests  
* python-dotenv
* Torchvision

| Lib / Import                                                                                                                 |                                                     License and link                                                      |
|------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------:|
| python-dotenv (`from dotenv import load_dotenv`)                                                                             |                  MIT — [github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)                   |
| python-telegram-bot (`from telegram import Update, ...` / `from telegram.ext import ...`)                                    | LGPLv3 — [github.com/python-telegram-bot/python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) |
| NumPy (`import numpy as np`)                                                                                                 |                              BSD — [github.com/numpy/numpy](https://github.com/numpy/numpy)                               |
| PyTorch (`import torch`, `import torch.nn as nn`, `from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler`) |                       BSD-style — [github.com/pytorch/pytorch](https://github.com/pytorch/pytorch)                        |
| Torchvision (`import torchvision.transforms as transforms`, `import torchvision.models as models`)                           |                        BSD-style — [github.com/pytorch/vision](https://github.com/pytorch/vision)                         |
| Pillow (PIL) (`from PIL import Image, ImageFile, UnidentifiedImageError`)                                                    |       PIL Software License (MIT-like) — [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow)        |

