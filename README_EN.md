# 🥗 FoodCalorieBot — Telegram Bot for Calorie Tracking

[![Tests](https://github.com/YOUR_USERNAME/CaloriesCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/CaloriesCalc/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **QA Automation Pet Project** — demonstrating testing, refactoring, and CI/CD skills through a working Telegram bot.

---

## 📖 Overview

FoodCalorieBot is a Telegram bot for tracking daily calorie intake with AI-powered food recognition from photos. This project showcases:

✅ **Clean Architecture** (layered separation: handlers, core, ml)  
✅ **85%+ Test Coverage** (Unit + Integration tests)  
✅ **CI/CD Pipeline** (automated test execution on push)  
✅ **Mocking External Dependencies** (Telegram API, SQLite)  
✅ **Async Testing** (pytest-asyncio)

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📅 Daily Calorie Limit | Set daily goals, get notifications when exceeded |
| ➕ Add Food Entries | Calculate calories based on product weight |
| 🔥 Daily Statistics | View consumed calories and food log for today |
| 🍗 Product Catalog | Add and search custom products in database |
| 📸 Food Recognition | Predict food type from photo using ML |
| 🧠 Model Training | Auto-collect dataset and fine-tune CNN model |

---

## 🛠 Tech Stack

### Core Technologies

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


### Dependencies & Licenses

| Library | Purpose | License |
|---------|---------|---------|
| `python-telegram-bot` | Telegram Bot API | LGPLv3 |
| `python-dotenv` | Environment variable management | MIT |
| `pytest` + plugins | Testing framework | MIT |
| `PyTorch` | ML model framework | BSD-3 |
| `torchvision` | Pre-trained models & transforms | BSD-3 |
| `Pillow` | Image processing | HPND |
| `pymorphy3` | Russian text lemmatization | Apache 2.0 |

---

## 📁 Project Structure

```angular2html
CaloriesCalc/
├── bot/
│ ├── main.py # Entry point
│ ├── handlers.py # Command handlers (with Dependency Injection)
│ ├── keyboards.py # Keyboard factory
│ ├── states.py # Dialog state Enum
│ └── str_utils.py # Helper utilities
├── core/
│ ├── database.py # SQLite operations (testable)
│ ├── calculator.py # Business logic for calculations
│ └── validator.py # User input validation
├── ml/
│ ├── food_model.py # CNN model for food recognition
│ ├── dataset_collector.py # Dataset collection & labeling
│ └── data_loader.py # Data loading & augmentation
├── tests/
│ ├── conftest.py # Shared fixtures (DB, mocks)
│ ├── test_calculator.py # Unit tests for business logic
│ ├── test_validator.py # Unit tests for input validation
│ ├── test_database.py # DB tests with temporary files
│ └── test_handlers.py # Integration tests with Telegram API mocks
├── .github/workflows/
│ └── ci.yml # CI/CD pipeline (GitHub Actions)
├── requirements.txt # Production dependencies
├── requirements-dev.txt # Development & testing dependencies
├── .gitignore # Ignored files
└── README.md # This file
```


---

## 🧪 Testing

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=bot --cov=core --cov-report=html

# Open coverage report in browser (Windows)
start htmlcov/index.html

# Run only handler tests
pytest tests/test_handlers.py -v

# Run with mocks and debug output
pytest -v -s --cov=bot --cov-report=term-missing
```

## 🚀 Quick Start

```angular2html
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/CaloriesCalc.git
cd CaloriesCalc

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up bot token
# Create a .env file with:
BOT_TOKEN=123456789:AAHdqTcvCH1vGWJxfSeofSAswK5PALnAt
LOG_LEVEL=INFO

# 5. Run the bot
python bot/main.py
```

