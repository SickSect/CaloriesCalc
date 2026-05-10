from telegram import KeyboardButton, ReplyKeyboardMarkup

from bot.translator import Translator


class Keyboards:
    """Фабрика клавиатур"""

    @staticmethod
    def get_start_keyboard(translator: Translator) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton(translator.get("keyboard.start"))]],
            resize_keyboard=True
        )

    @staticmethod
    def get_main_keyboard(translator: Translator) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton(translator.get("keyboard.setDailyCalories"))],
                [KeyboardButton(translator.get("keyboard.addCalories"))],
                [KeyboardButton(translator.get("keyboard.todayCalories"))],
                [KeyboardButton(translator.get("keyboard.addProduct"))],
                [KeyboardButton(translator.get("keyboard.askQuestion"))]
            ],
            resize_keyboard=True
        )

    @staticmethod
    def get_cancel_keyboard(translator: Translator) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton(translator.get("keyboard.cancel"))]],
            resize_keyboard=True
        )