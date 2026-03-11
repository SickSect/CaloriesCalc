import pytest
from core.validator import InputValidator, ValidationResult


class TestInputValidator:
    """Тесты на валидатор ввода"""

    # ===== Тесты валидации калорий =====

    def test_validate_calories_valid(self):
        """Валидное число"""
        result = InputValidator.validate_calories("2000")
        assert result.is_valid == True
        assert result.error_message is None

    def test_validate_calories_zero(self):
        """Ноль - допустимо"""
        result = InputValidator.validate_calories("0")
        assert result.is_valid == True

    def test_validate_calories_negative(self):
        """Отрицательное число"""
        result = InputValidator.validate_calories("-100")
        assert result.is_valid == False
        assert "отрицательными" in result.error_message

    def test_validate_calories_too_large(self):
        """Слишком большое число"""
        result = InputValidator.validate_calories("999999")
        assert result.is_valid == False
        assert "Максимальное" in result.error_message

    def test_validate_calories_not_number(self):
        """Не число"""
        result = InputValidator.validate_calories("abc")
        assert result.is_valid == False
        assert "Введите число" in result.error_message

    def test_validate_calories_empty(self):
        """Пустая строка"""
        result = InputValidator.validate_calories("")
        assert result.is_valid == False

    # ===== Тесты валидации веса =====

    def test_validate_weight_valid(self):
        """Валидный вес"""
        result = InputValidator.validate_weight("150")
        assert result.is_valid == True

    def test_validate_weight_decimal(self):
        """Дробный вес"""
        result = InputValidator.validate_weight("150.5")
        assert result.is_valid == True

    def test_validate_weight_zero(self):
        """Вес = 0"""
        result = InputValidator.validate_weight("0")
        assert result.is_valid == False
        assert "больше 0" in result.error_message

    def test_validate_weight_negative(self):
        """Отрицательный вес"""
        result = InputValidator.validate_weight("-50")
        assert result.is_valid == False

    # ===== Тесты валидации названия продукта =====

    def test_validate_product_name_valid(self):
        """Валидное название"""
        result = InputValidator.validate_product_name("Яблоко")
        assert result.is_valid == True

    def test_validate_product_name_empty(self):
        """Пустая строка"""
        result = InputValidator.validate_product_name("")
        assert result.is_valid == False
        assert "пустым" in result.error_message

    def test_validate_product_name_whitespace(self):
        """Только пробелы"""
        result = InputValidator.validate_product_name("   ")
        assert result.is_valid == False

    def test_validate_product_name_too_long(self):
        """Слишком длинное"""
        long_name = "А" * 100
        result = InputValidator.validate_product_name(long_name)
        assert result.is_valid == False
        assert "длина" in result.error_message.lower()

    def test_validate_product_name_max_length(self):
        """Максимальная длина (граница)"""
        max_name = "А" * 60
        result = InputValidator.validate_product_name(max_name)
        assert result.is_valid == True