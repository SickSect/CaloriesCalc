# 🥗 FoodCalorieBot — Telegram-бот для учёта калорий

[![Tests](https://github.com/YOUR_USERNAME/CaloriesCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/CaloriesCalc/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **QA Automation Pet Project** — демонстрация навыков тестирования, рефакторинга и CI/CD на примере работающего Telegram-бота.

---

## 📖 Описание

FoodCalorieBot — это Telegram-бот для подсчета калорий с функцией распознавания еды по фото. Проект демонстрирует:

✅ **Чистую архитектуру** (разделение на слои: handlers, core, ml)  
✅ **Покрытие тестами 85%+** (Unit + Integration)  
✅ **CI/CD пайплайн** (автозапуск тестов при push)  
✅ **Мокирование внешних зависимостей** (Telegram API, SQLite)  
✅ **Асинхронное тестирование** (pytest-asyncio)

---

## 🚀 Возможности бота

| Функция | Описание |
|---------|----------|
| 📅 Лимит калорий | Установка дневной нормы, уведомления о превышении |
| ➕ Добавление еды | Расчет калорий по весу продукта |
| 🔥 Статистика | Просмотр съеденных калорий за день |
| 🍗 Каталог продуктов | Добавление и поиск продуктов в базе |
| 📸 Распознавание еды | Предсказание продукта по фото (ML) |
| 🧠 Обучение модели | Авто-сбор датасета и дообучение CNN |

---

## 🛠 Технологический стек

### Основные технологии

```angular2html
┌─────────────────────────────────────┐
│ 🤖 Bot Framework │ python-telegram-bot v22 │
│ 🗄 Database │ SQLite │
│ 🧠 ML │ PyTorch, torchvision │
│ 🔧 Testing │ pytest, pytest-asyncio │
│ 🔄 CI/CD │ GitHub Actions │
│ 📊 Coverage │ pytest-cov, Codecov │
└─────────────────────────────────────┘
```


### Зависимости и лицензии

| Библиотека | Назначение | Лицензия |
|------------|------------|----------|
| `python-telegram-bot` | Telegram Bot API | LGPLv3 |
| `python-dotenv` | Управление переменными окружения | MIT |
| `pytest` + плагины | Тестирование | MIT |
| `PyTorch` | ML-модель | BSD-3 |
| `torchvision` | Претренированные модели | BSD-3 |
| `Pillow` | Обработка изображений | HPND |
| `pymorphy3` | Лемматизация русского текста | Apache 2.0 |

---

## 📁 Структура проекта

```angular2html
CaloriesCalc/
├── bot/
│ ├── main.py # Точка входа
│ ├── handlers.py # Обработчики команд (с Dependency Injection)
│ ├── keyboards.py # Фабрика клавиатур
│ ├── states.py # Enum состояний диалога
│ └── str_utils.py # Вспомогательные функции
├── core/
│ ├── database.py # Работа с SQLite (тестируемая)
│ ├── calculator.py # Бизнес-логика расчётов
│ └── validator.py # Валидация пользовательского ввода
├── ml/
│ ├── food_model.py # CNN модель для распознавания
│ ├── dataset_collector.py # Сбор и разметка датасета
│ └── data_loader.py # Загрузка и аугментация данных
├── tests/
│ ├── conftest.py # Общие фикстуры (БД, моки)
│ ├── test_calculator.py # Unit-тесты на логику
│ ├── test_validator.py # Unit-тесты на валидацию
│ ├── test_database.py # Тесты БД с временными файлами
│ └── test_handlers.py # Integration-тесты с моками Telegram
├── .github/workflows/
│ └── ci.yml # CI/CD пайплайн (GitHub Actions)
├── requirements.txt # Основные зависимости
├── requirements-dev.txt # Зависимости для тестов
├── .gitignore # Исключаемые файлы
└── README.md # Этот файл
```



---

## 🧪 Тестирование

### Запуск тестов

```bash
# Установить зависимости для разработки
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Запустить все тесты с выводом подробностей
pytest -v

# Запустить с отчетом о покрытии
pytest --cov=bot --cov=core --cov-report=html

# Открыть отчет в браузере (Windows)
start htmlcov/index.html

# Запустить только тесты хендлеров
pytest tests/test_handlers.py -v

# Запустить с моками и отладкой
pytest -v -s --cov=bot --cov-report=term-missing
```
--

## 🚀 Быстрый старт

`````### 1. Клонирование
git clone https://github.com/YOU/CaloriesCalc.git
cd CaloriesCalc

### 2. Виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows

### 3. Зависимости
pip install -r requirements.txt

### 4. Токен бота
Создай файл `.env`:
BOT_TOKEN=123456:AAH...
LOG_LEVEL=INFO 

### 5. Запуск
python bot/main.py```

