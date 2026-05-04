# Unit-тесты в Python — краткая шпаргалка

## Что такое unit-тест

Тест проверяет **одну конкретную функцию или метод в изоляции** от остального кода.
«В изоляции» — значит без реальной БД, без реального Telegram, без реальной сети.
Всё внешнее заменяется на фейки (моки).

---

## Структура теста — AAA

Любой тест строится по трём шагам:

```python
def test_calculate_calories():
    # Arrange — подготовка данных
    calories_per_100 = 200
    weight = 150

    # Act — вызов тестируемого кода
    result = CalorieCalculator.calculate(calories_per_100, weight)

    # Assert — проверка результата
    assert result == 300.0
```

Если тест падает — сразу видно на каком шаге.

---

## Базовые assert'ы

```python
assert result == 300.0          # равенство
assert result != 0              # неравенство
assert result is None           # None
assert result is not None       # не None
assert len(items) == 3          # длина
assert "ошибка" in message      # подстрока
assert isinstance(x, int)       # тип
assert value > 0                # сравнение
assert validation.is_valid      # bool True
assert not validation.is_valid  # bool False
```

---

## pytest — запуск тестов

```bash
pytest                                    # все тесты
pytest -v                                 # подробный вывод (имена тестов)
pytest -s                                 # показывать print() внутри тестов
pytest tests/test_calculator.py           # один файл
pytest tests/test_calculator.py::TestCalorieCalculator::test_calculate_standard  # один тест
pytest --cov=bot --cov=core --cov-report=term-missing   # с покрытием
```

---

## Классы тестов

Тесты можно группировать в классы — удобно когда много тестов на один модуль:

```python
class TestCalorieCalculator:
    """Тесты калькулятора калорий"""

    def test_calculate_standard(self):
        result = CalorieCalculator.calculate(200, 150)
        assert result == 300.0

    def test_calculate_zero_weight(self):
        result = CalorieCalculator.calculate(200, 0)
        assert result == 0.0

    def test_calculate_rounding(self):
        result = CalorieCalculator.calculate(33.333, 100)
        assert result == 33.33
```

Класс — просто организация, не несёт особой логики.
Каждый метод начинается с `test_` — pytest находит их автоматически.

---

## Fixtures — переиспользуемые данные

Фикстура создаётся один раз и передаётся в тест как аргумент:

```python
import pytest
from core.db import Database

@pytest.fixture
def db():
    """БД в памяти — создаётся заново для каждого теста"""
    database = Database(db_path=":memory:")
    database.init_db(skip_init_data=True)
    yield database       # ← тест выполняется здесь
    database.close()     # ← teardown: очистка после теста

def test_add_user(db):   # ← pytest видит аргумент db и подставляет фикстуру
    db.add_user(12345)
    assert db.check_user_exists(12345) is True
```

`":memory:"` — SQLite в памяти, не пишет на диск.
Каждый тест получает **чистую** БД.

---

## conftest.py — общие фикстуры

Если фикстура нужна в нескольких тест-файлах, выноси в `conftest.py`:

```python
# tests/conftest.py
import pytest
from core.db import Database
from core.calculator import CalorieCalculator

@pytest.fixture
def db():
    database = Database(db_path=":memory:")
    database.init_db(skip_init_data=True)
    yield database
    database.close()

@pytest.fixture
def calculator():
    return CalorieCalculator()
```

pytest находит `conftest.py` автоматически — никаких импортов не нужно.

---

## Моки — замена внешних зависимостей

### unittest.mock.MagicMock — синхронный мок

```python
from unittest.mock import MagicMock

def test_handler_adds_user():
    db = MagicMock()
    db.check_user_exists.return_value = False  # притворяемся что пользователя нет

    # вызываем код который использует db
    # проверяем что add_user был вызван
    db.add_user.assert_called_once_with(12345)
```

`MagicMock` — объект-пустышка. Любой вызов на нём вернёт ещё один мок,
если не задать `return_value`.

### AsyncMock — для async функций

```python
from unittest.mock import AsyncMock

async def test_async_handler():
    db = MagicMock()
    db.check_user_exists = AsyncMock(return_value=False)
    db.add_user = AsyncMock()

    await handler.handle_start_button(update, context)

    db.add_user.assert_called_once()
```

Обычный `MagicMock` нельзя `await`'ить — нужен `AsyncMock`.

### patch — временная подмена в модуле

```python
from unittest.mock import patch

def test_something_without_real_network():
    with patch("core.db.get_json_config") as mock_config:
        mock_config.return_value = []   # пустой список продуктов
        db = Database(":memory:")
        db.init_db()
        # тест не полезет в реальный файл
```

`patch` подменяет объект **только на время блока `with`**, потом возвращает оригинал.

---

## Async тесты — pytest-asyncio

Для тестирования `async def` функций:

```python
import pytest

@pytest.mark.asyncio          # ← обязательный декоратор
async def test_async_db():
    db = Database(":memory:")
    await db.init_db()
    await db.add_user(12345)
    result = await db.check_user_exists(12345)
    assert result is True
```

Конфиг в `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto   # ← тогда @pytest.mark.asyncio можно не писать
```

---

## Тест на исключение

```python
def test_invalid_calories_raises():
    with pytest.raises(ValueError):
        CalorieCalculator.calculate(-100, 50)

def test_validation_error_message():
    result = InputValidator.validate_calories("-5")
    assert not result.is_valid
    assert "отрицательными" in result.error_message
```

---

## Что тестировать, что нет

**Тестировать:**
- Бизнес-логику: `CalorieCalculator.calculate`, `InputValidator.*`
- SQL-методы: `db.add_user`, `db.get_today_calories` — через `:memory:`
- Граничные случаи: ноль, максимум, пустая строка, None
- Ошибочные пути: невалидный ввод, несуществующий пользователь

**Не тестировать:**
- Реальный Telegram API (только через моки)
- Реальный Ollama (только через моки)
- Форматирование строк без логики (тривиально)
- Код который просто вызывает другой код без условий

---

## Пример из проекта: как устроен test_handlers.py

```python
# Создание фейкового Update объекта Telegram
@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()  # ← reply_text это async
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}  # ← пустой словарь для данных диалога
    return context

@pytest.mark.asyncio
async def test_start_creates_user_if_not_exists(mock_update, mock_context, db):
    handlers = BotHandlers(db=db, calculator=CalorieCalculator())

    # Пользователя нет → хендлер должен его создать
    await handlers.handle_start_button(mock_update, mock_context)

    assert await db.check_user_exists(12345) is True
```

Ключевые приёмы:
- `MagicMock(spec=Update)` — мок который знает интерфейс Update, не даст вызвать несуществующие методы
- `context.user_data = {}` — реальный словарь, не мок, потому что хендлеры в него пишут
- `AsyncMock()` для любого метода который вызывается через `await`
