from telegram import KeyboardButton, ReplyKeyboardMarkup


class Keyboards:
    """Фабрика клавиатур"""

    @staticmethod
    def get_start_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("Начать")]],
            resize_keyboard=True
        )

    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton("📅 Установить суточные калории")],
                [KeyboardButton("➕ Добавить калории")],
                [KeyboardButton("🔥 Калории сегодня")],
                [KeyboardButton("🍗 Добавить продукт")],
                [KeyboardButton("📸 Распознать еду")]
            ],
            resize_keyboard=True
        )

    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("❌ Отмена")]],
            resize_keyboard=True
        )