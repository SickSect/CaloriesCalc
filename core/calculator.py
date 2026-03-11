class CalorieCalculator:
    """Бизнес-логика расчёта калорий"""

    @staticmethod
    def calculate(calories_per_100: float, weight: float) -> float:
        """
        Расчёт калорийности порции

        Args:
            calories_per_100: калорийность на 100г
            weight: вес порции в граммах

        Returns:
            Общая калорийность порции
        """
        return round(calories_per_100 * weight / 100, 2)

    @staticmethod
    def calculate_total(today_calories: list, limit: int = None) -> dict:
        """
        Расчёт итогов за день

        Args:
            today_calories: список [продукт, калории]
            limit: дневной лимит (опционально)

        Returns:
            Словарь с отчётом
        """
        total = sum(item[1] for item in today_calories) if today_calories else 0

        result = {
            'total': total,
            'items_count': len(today_calories) if today_calories else 0
        }

        if limit:
            result['limit'] = limit
            result['remaining'] = max(0, limit - total)
            result['exceeded'] = total > limit

        return result