import pytest
from core.calculator import CalorieCalculator


class TestCalorieCalculator:
    """Тесты на калькулятор калорий"""

    def test_calculate_standard(self):
        """Обычный расчет: 200 ккал/100г * 150г = 300 ккал"""
        result = CalorieCalculator.calculate(200, 150)
        assert result == 300.0

    def test_calculate_zero_weight(self):
        """Вес = 0"""
        result = CalorieCalculator.calculate(200, 0)
        assert result == 0.0

    def test_calculate_decimal(self):
        """Дробные значения"""
        result = CalorieCalculator.calculate(33.33, 100)
        assert result == 33.33

    def test_calculate_rounding(self):
        """Округление до 2 знаков"""
        result = CalorieCalculator.calculate(33.333, 100)
        assert result == 33.33

    def test_calculate_large_values(self):
        """Большие значения"""
        result = CalorieCalculator.calculate(500, 1000)
        assert result == 5000.0