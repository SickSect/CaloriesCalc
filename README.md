# 🥗 FoodCalorieBot — Telegram Calorie Tracker with AI Advisor

[![Tests](https://github.com/SickSect/CaloriesCalc/actions/workflows/ci.yml/badge.svg)](https://github.com/SickSect/CaloriesCalc/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> A Telegram bot for tracking daily nutrition with a local AI advisor powered by Ollama. No external AI APIs — everything runs on your machine.

---

## 📖 Overview

FoodCalorieBot helps you track what you eat, stay within your calorie goal, and get personalized nutrition advice from a local LLM. The bot is live and running — you can try it right now.

**What makes this project interesting:**

- 🤖 **Local AI integration** — Ollama + LLaMA 3 for nutrition analysis, no API keys needed
- 🧪 **85%+ test coverage** — unit and integration tests with mocked Telegram API
- ⚡ **Fully async** — built on `python-telegram-bot` v22 with `asyncio`
- 🔄 **CI/CD** — GitHub Actions runs tests on every push

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📅 Daily calorie limit | Set your daily goal, get notified when exceeded |
| ➕ Food log | Add meals with weight, calories calculated automatically |
| 🔥 Daily stats | View calories consumed and full food log for today |
| 🍗 Product catalog | Add and search custom products in local database |
| 🧠 AI advisor | Ask the local LLM to analyze your diet and suggest improvements |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Bot framework | `python-telegram-bot` v22 |
| Database | SQLite (via JDBC-style abstraction) |
| AI | Ollama + LLaMA 3.2 (local) |
| HTTP client | `httpx` (async) |
| Testing | `pytest`, `pytest-asyncio`, `pytest-cov` |
| CI/CD | GitHub Actions |
| Text processing | `pymorphy3` (Russian lemmatization) |

---

## 📁 Project Structure

```
CaloriesCalc/
├── bot/
│   ├── main.py           # Entry point, app builder
│   ├── handlers.py       # Command handlers (Dependency Injection)
│   ├── keyboards.py      # Keyboard factory
│   └── states.py         # Dialog state enum
├── core/
│   ├── db.py             # SQLite operations
│   ├── calculator.py     # Calorie calculation logic
│   ├── validator.py      # User input validation
│   └── str_utils.py      # Message formatting helpers
├── ai/
│   └── advisor.py        # Ollama integration, prompt builder
├── tests/
│   ├── conftest.py       # Shared fixtures (in-memory DB, mocks)
│   ├── test_calculator.py
│   ├── test_validator.py
│   ├── test_db.py
│   └── test_handlers.py  # Integration tests with mocked Telegram API
├── .github/workflows/
│   └── ci.yml            # GitHub Actions pipeline
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

---

## ⚡ Quick Start

### Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and set up

```bash
git clone https://github.com/SickSect/CaloriesCalc.git
cd CaloriesCalc

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN
```

```env
BOT_TOKEN=123456789:AAH...
LOG_LEVEL=INFO
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3. Pull the AI model

```bash
ollama pull llama3.2
```

### 4. Run

```bash
python bot/main.py
```

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest -v

# With coverage report
pytest --cov=bot --cov=core --cov-report=term-missing

# Only unit tests
pytest tests/test_calculator.py tests/test_validator.py -v
```

Tests use in-memory SQLite and mocked Telegram API — no real bot token needed.

---

## 🔮 Roadmap

- [ ] КБЖУ tracking (proteins, fats, carbs) alongside calories
- [ ] Weekly statistics and progress summary
- [ ] Food photo recognition via Ollama vision model (LLaVA)
- [ ] PostgreSQL support for multi-user deployments
- [ ] Docker Compose setup

---

## 📄 License

MIT — see [LICENSE](LICENSE)
