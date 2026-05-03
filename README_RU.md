# 🥗 FoodCalorieBot — Telegram-бот для трекинга питания с AI-советником

[![Tests](https://github.com/YOUR_USERNAME/CaloriesCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/CaloriesCalc/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Telegram-бот для трекинга калорий с локальным AI-советником на базе Ollama. Без внешних API — всё работает на твоей машине.

---

## 📖 Описание

FoodCalorieBot помогает следить за питанием, не выходить за рамки дневной нормы и получать персональные рекомендации от локальной языковой модели. Бот живой — можно зайти и попробовать прямо сейчас.

**Что интересного в проекте:**

- 🤖 **Локальный AI** — Ollama + LLaMA 3 для анализа рациона, без API-ключей
- 🧪 **Покрытие тестами 85%+** — unit и integration тесты с моками Telegram API
- ⚡ **Полностью async** — `python-telegram-bot` v22 на базе `asyncio`
- 🔄 **CI/CD** — GitHub Actions запускает тесты при каждом пуше

---

## 🚀 Возможности

| Функция | Описание |
|---------|----------|
| 📅 Дневной лимит | Установи норму калорий, получай уведомления при превышении |
| ➕ Журнал еды | Добавляй приёмы пищи с весом, калории считаются автоматически |
| 🔥 Статистика дня | Просмотр съеденных калорий и полного списка за день |
| 🍗 Каталог продуктов | Добавление и поиск продуктов в локальной базе |
| 🧠 AI-советник | Попроси локальную LLM проанализировать твой рацион и дать рекомендации |

---

## 🛠 Технологический стек

| Слой | Технология |
|------|------------|
| Bot framework | `python-telegram-bot` v22 |
| База данных | SQLite |
| AI | Ollama + LLaMA 3.2 (локально) |
| HTTP-клиент | `httpx` (async) |
| Тестирование | `pytest`, `pytest-asyncio`, `pytest-cov` |
| CI/CD | GitHub Actions |
| Обработка текста | `pymorphy3` (лемматизация русского) |

---

## 📁 Структура проекта

```
CaloriesCalc/
├── bot/
│   ├── main.py           # Точка входа, сборка приложения
│   ├── handlers.py       # Обработчики команд (Dependency Injection)
│   ├── keyboards.py      # Фабрика клавиатур
│   └── states.py         # Enum состояний диалога
├── core/
│   ├── db.py             # Работа с SQLite
│   ├── calculator.py     # Логика расчёта калорий
│   ├── validator.py      # Валидация пользовательского ввода
│   └── str_utils.py      # Форматирование сообщений
├── ai/
│   └── advisor.py        # Интеграция с Ollama, построение промптов
├── tests/
│   ├── conftest.py       # Общие фикстуры (БД в памяти, моки)
│   ├── test_calculator.py
│   ├── test_validator.py
│   ├── test_db.py
│   └── test_handlers.py  # Integration-тесты с моками Telegram API
├── .github/workflows/
│   └── ci.yml            # GitHub Actions пайплайн
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

---

## ⚡ Быстрый старт

### Требования

- Python 3.11+
- [Ollama](https://ollama.com) установлена и запущена
- Токен Telegram-бота от [@BotFather](https://t.me/BotFather)

### 1. Клонирование и окружение

```bash
git clone https://github.com/YOUR_USERNAME/CaloriesCalc.git
cd CaloriesCalc

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

### 2. Настройка

```bash
cp .env.example .env
# Открой .env и вставь свой BOT_TOKEN
```

```env
BOT_TOKEN=123456789:AAH...
LOG_LEVEL=INFO
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3. Скачать AI-модель

```bash
ollama pull llama3.2
```

### 4. Запуск

```bash
python bot/main.py
```

---

## 🧪 Тестирование

```bash
# Установить зависимости для разработки
pip install -r requirements-dev.txt

# Запустить все тесты
pytest -v

# С отчётом о покрытии
pytest --cov=bot --cov=core --cov-report=term-missing

# Только unit-тесты
pytest tests/test_calculator.py tests/test_validator.py -v
```

Тесты используют SQLite в памяти и мок Telegram API — реальный токен не нужен.

---

## 🔮 Планы

- [ ] Трекинг КБЖУ (белки, жиры, углеводы) помимо калорий
- [ ] Недельная статистика и сводка прогресса
- [ ] Распознавание еды по фото через Ollama vision (LLaVA)
- [ ] Поддержка PostgreSQL для многопользовательских деплоев
- [ ] Docker Compose для запуска одной командой

---

## 📄 Лицензия

MIT — см. [LICENSE](LICENSE)
