import re

from bot.translator import Translator


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
    def validate_calories(value: str, translator: Translator) -> ValidationResult:
        """Валидация ввода калорий"""
        try:
            calories = int(value)
            if calories < InputValidator.MIN_CALORIES:
                return ValidationResult(False, translator.get("validator.caloriesBelowZero"))
            if calories > InputValidator.MAX_CALORIES:
                return ValidationResult(False, translator.get("validator.moreThanMaxCalories"))
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, translator.get("validator.enterNum"))

    @staticmethod
    def validate_weight(value: str, translator: Translator = None) -> ValidationResult:
        """Валидация веса продукта"""
        try:
            weight = float(value)
            if weight < InputValidator.MIN_WEIGHT:
                return ValidationResult(False, translator.get("validator.weightBelowZero"))
            if weight > InputValidator.MAX_WEIGHT:
                return ValidationResult(False, translator.get("validator.moreThanMaxWeight"))
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, translator.get("validator.enterNum"))

    @staticmethod
    def validate_product_name(name: str, translator: Translator = None) -> ValidationResult:
        """Валидация названия продукта"""
        if not name or not name.strip():
            return ValidationResult(False, translator.get("validator.emptyName"))
        if len(name.strip()) > InputValidator.MAX_PRODUCT_NAME_LENGTH:
            return ValidationResult(False, translator.get("validator.moreThanMaxLength"))
        return ValidationResult(True)