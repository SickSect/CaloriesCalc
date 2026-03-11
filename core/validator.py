import re

def check_if_digits_only(value):
    if re.match(r'^\d+$', value):
        return True
    else:
        return False


from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    error_message: Optional[str] = None


class InputValidator:
    """Валидация пользовательского ввода"""

    MAX_PRODUCT_NAME_LENGTH = 60
    MIN_CALORIES = 0
    MAX_CALORIES = 10000
    MIN_WEIGHT = 1
    MAX_WEIGHT = 10000

    @staticmethod
    def validate_calories(value: str) -> ValidationResult:
        """Валидация ввода калорий"""
        try:
            calories = int(value)
            if calories < InputValidator.MIN_CALORIES:
                return ValidationResult(False, "Калории не могут быть отрицательными")
            if calories > InputValidator.MAX_CALORIES:
                return ValidationResult(False, f"Максимальное значение: {InputValidator.MAX_CALORIES}")
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, "Введите число")

    @staticmethod
    def validate_weight(value: str) -> ValidationResult:
        """Валидация веса продукта"""
        try:
            weight = float(value)
            if weight < InputValidator.MIN_WEIGHT:
                return ValidationResult(False, "Вес должен быть больше 0")
            if weight > InputValidator.MAX_WEIGHT:
                return ValidationResult(False, f"Максимальный вес: {InputValidator.MAX_WEIGHT}г")
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, "Введите число")

    @staticmethod
    def validate_product_name(name: str) -> ValidationResult:
        """Валидация названия продукта"""
        if not name or not name.strip():
            return ValidationResult(False, "Название не может быть пустым")
        if len(name.strip()) > InputValidator.MAX_PRODUCT_NAME_LENGTH:
            return ValidationResult(False, f"Максимальная длина: {InputValidator.MAX_PRODUCT_NAME_LENGTH} символов")
        return ValidationResult(True)