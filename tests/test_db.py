import pytest
import sqlite3
import tempfile
import os

from core.db import Database


@pytest.fixture(scope="function")
def test_db():
    """
    Фикстура: создает временную БД в файле для каждого теста.
    Корректно закрывает соединения перед удалением файла (Windows-compatible).
    """
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_path = temp_file.name
    temp_file.close()

    # Создаем БД и инициализируем
    db = Database(temp_path)
    db.init_db(skip_init_data=True)

    yield db

    # === КОРРЕКТНАЯ ОЧИСТКА ДЛЯ WINDOWS ===
    # 1. Явно закрываем все соединения (если есть метод close)
    if hasattr(db, 'close'):
        db.close()

    # 2. Даем ОС время освободить файл
    import time
    time.sleep(0.1)

    # 3. Пробуем удалить файл с повторными попытками
    import gc
    gc.collect()  # Принудительный сборщик мусора

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            break
        except PermissionError:
            if attempt == max_attempts - 1:
                pass  # Игнорируем, Windows сам очистит temp позже
            time.sleep(0.2 * (attempt + 1))


class TestDatabase:
    """Тесты на работу с базой данных"""

    def test_add_user(self, test_db):
        """Добавление нового пользователя"""
        result = test_db.add_user(12345)
        assert result is not None

    def test_check_user_exists_true(self, test_db):
        """Проверка: пользователь существует"""
        test_db.add_user(12345)
        assert test_db.check_user_exists(12345) == True

    def test_check_user_exists_false(self, test_db):
        """Проверка: пользователь не существует"""
        assert test_db.check_user_exists(99999) == False

    def test_set_daily_calories(self, test_db):
        """Установка дневного лимита калорий"""
        test_db.add_user(12345)
        test_db.set_daily_calories(12345, 2500)
        limit = test_db.get_daily_limit(12345)
        assert limit == 2500

    def test_get_daily_limit_not_set(self, test_db):
        """Лимит не установлен (возвращает None)"""
        test_db.add_user(12345)
        limit = test_db.get_daily_limit(12345)
        assert limit is None

    def test_get_daily_limit_zero(self, test_db):
        """Лимит = 0 (возвращает None)"""
        test_db.add_user(12345)
        test_db.set_daily_calories(12345, 0)
        limit = test_db.get_daily_limit(12345)
        assert limit is None

    def test_add_product_success(self, test_db):
        """Добавление нового продукта"""
        result = test_db.add_product("Яблоко", 52)
        assert result == True

    def test_add_product_duplicate(self, test_db):
        """Попытка добавить дубликат продукта"""
        test_db.add_product("Яблоко", 52)
        result = test_db.add_product("Яблоко", 60)
        assert result == False

    def test_check_product_exists_true(self, test_db):
        """Проверка: продукт существует"""
        test_db.add_product("Банан", 89)
        assert test_db.check_product_exists("Банан") == True

    def test_check_product_exists_false(self, test_db):
        """Проверка: продукт не существует"""
        assert test_db.check_product_exists("Неизвестный") == False

    def test_get_product_info(self, test_db):
        """Получение информации о продукте"""
        test_db.add_product("Гречка", 343)
        info = test_db.get_product_info("Гречка")
        assert info is not None
        assert info[1] == 343
        assert info[2] == "Гречка"

    def test_add_calories_for_today_first_entry(self, test_db):
        """Первая запись калорий за сегодня"""
        test_db.add_user(12345)
        test_db.add_calories_for_today(12345, 500, "Овсянка")
        report = test_db.get_today_calories(12345)
        assert report is not None
        assert len(report) == 1
        assert report[0][0] == "Овсянка"
        assert report[0][1] == 500

    def test_add_calories_for_today_second_entry(self, test_db):
        """Вторая запись калорий (накопление)"""
        test_db.add_user(12345)
        test_db.add_calories_for_today(12345, 500, "Овсянка")
        test_db.add_calories_for_today(12345, 300, "Яблоко")
        report = test_db.get_today_calories(12345)
        assert len(report) == 2
        assert report[1][1] == 800

    def test_get_today_calories_empty(self, test_db):
        """Нет записей за сегодня"""
        test_db.add_user(12345)
        report = test_db.get_today_calories(12345)
        assert report is None

    def test_get_products_info(self, test_db):
        """Получение списка всех продуктов"""
        test_db.add_product("Яблоко", 52)
        test_db.add_product("Банан", 89)
        products = test_db.get_products_info()
        assert len(products) == 2