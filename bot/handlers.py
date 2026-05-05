import asyncio
import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from bot.states import DialogState
from bot.keyboards import Keyboards
from core.calculator import CalorieCalculator
from core.db import Database
from core.str_utils import send_card, print_daily_report
from core.validator import InputValidator, ValidationResult

logger = logging.getLogger(__name__)


class BotHandlers:
    """Обработчики команд с внедрением зависимостей"""

    def __init__(self, db: Database, calculator: CalorieCalculator):
        self.db = db
        self.calculator = calculator
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock(self, uid: int) -> asyncio.Lock:
        return self._locks.setdefault(uid, asyncio.Lock())

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        await send_card(
            update,
            context,
            title="ℹ️ Справка",
            fields=[
                ("📅", "Установить суточные калории"),
                ("➕", "Добавить калории"),
                ("🔥", "Калории сегодня"),
                ("📸", "Распознать еду")
            ],
            footer="Выберите действие ниже ⬇️",
            keyboard=Keyboards.get_start_keyboard()
        )

    async def handle_start_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Начать'"""
        user_id = update.effective_user.id
        if not await self.db.check_user_exists(user_id):
            await self.db.add_user(user_id)

        await send_card(
            update,
            context,
            title="✅ Успешно",
            fields=[("👤", "Добавил вас!")],
            footer="Выберите следующее действие ⬇️",
            keyboard=Keyboards.get_main_keyboard()
        )

    async def handle_today_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр калорий за сегодня"""
        user_id = update.effective_user.id
        if not await self.db.check_user_exists(user_id):
            await self.db.add_user(user_id)

        report = await self.db.get_today_calories(user_id)
        limit = await self.db.get_daily_limit(user_id)

        if report:
            text = print_daily_report(report)
            if limit:
                text += f"\nВаш дневной лимит: {limit} калорий"
            await update.message.reply_text(text, reply_markup=Keyboards.get_main_keyboard())
        else:
            await update.message.reply_text("Сегодня калории не записаны", reply_markup=Keyboards.get_main_keyboard())

    async def start_calories_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало установки суточных калорий"""
        await send_card(
            update,
            context,
            title="Ввод калорий",
            fields=[("🔥", "Пожалуйста, введите количество калорий:")],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=Keyboards.get_cancel_keyboard()
        )
        return DialogState.SET_CALORIES

    async def set_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода суточных калорий"""
        user_id = update.effective_user.id

        # ← ДОБАВЬ: создаём пользователя, если нет
        if not await self.db.check_user_exists(user_id):
            await self.db.add_user(user_id)

        text_input = update.message.text

        validation: ValidationResult = InputValidator.validate_calories(text_input)

        if not validation.is_valid:
            await send_card(
                update,
                context,
                title="Ошибка ввода",
                fields=[("✏️", validation.error_message)],
                footer="Для отмены используйте кнопку ниже ⬇️",
                keyboard=Keyboards.get_cancel_keyboard()
            )
            return DialogState.SET_CALORIES

        calories = int(text_input)
        await self.db.set_daily_calories(user_id, calories)

        await send_card(
            update,
            context,
            title="Цель установлена ✅",
            fields=[("🔥", f"Установлено {calories} ккал в день")],
            footer="Выберите следующее действие ⬇️",
            keyboard=Keyboards.get_main_keyboard()
        )
        return ConversationHandler.END

    async def start_product_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления продукта"""
        await send_card(
            update,
            context,
            title="Ввод продукта",
            fields=[("📛", "Пожалуйста, введите название продукта:")],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=Keyboards.get_cancel_keyboard()
        )
        return DialogState.SET_PRODUCT_NAME

    async def set_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка названия продукта"""
        text_input = update.message.text.strip()

        validation: ValidationResult = InputValidator.validate_product_name(text_input)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard())
            return DialogState.SET_PRODUCT_NAME

        context.user_data["product_name"] = text_input

        if await self.db.check_product_exists(text_input):
            product_info = await self.db.get_product_info(text_input)
            await update.message.reply_text(
                f"🥦 <b>Информация о продукте</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📛 <b>Название:</b> <i>{product_info[2]}</i>\n"
                f"🔥 <b>Калорийность:</b> <code>{product_info[1]} ккал / 100 г</code>\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Введите вес продукта в граммах ⬇️",
                parse_mode="HTML",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            context.user_data["calories_per_hundred"] = product_info[1]
            return DialogState.SET_PRODUCT_WEIGHT
        else:
            await update.message.reply_text(
                "Продукт не найден. Введите его калорийность на 100 грамм:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return DialogState.SET_TODAY_CALORIES

    async def set_product_weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка веса продукта"""
        text_input = update.message.text.strip()

        validation: ValidationResult = InputValidator.validate_weight(text_input)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard())
            return DialogState.SET_PRODUCT_WEIGHT

        weight = float(text_input)
        calories = self.calculator.calculate(
            float(context.user_data["calories_per_hundred"]),
            weight
        )

        await self.db.add_calories_for_today(
            update.effective_user.id,
            calories,
            context.user_data["product_name"]
        )

        await send_card(
            update,
            context,
            title="Запись добавлена!",
            fields=[
                ("📛 Продукт:", context.user_data["product_name"]),
                ("🔥 Калорийность:", f"{calories} ккал")
            ],
            footer="Выберите следующее действие",
            keyboard=Keyboards.get_main_keyboard()
        )
        return ConversationHandler.END

    async def add_calories_for_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода калорийности для нового продукта"""
        text_input = update.message.text.strip()

        validation: ValidationResult = InputValidator.validate_calories(text_input)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard())
            return DialogState.SET_TODAY_CALORIES

        calories = int(text_input)
        context.user_data["calories_per_hundred"] = calories

        # Добавляем продукт в базу
        await self.db.add_product(context.user_data["product_name"], calories)

        await send_card(
            update,
            context,
            title="Ввод веса",
            fields=[("⚖️", "Введите вес продукта:")],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=Keyboards.get_cancel_keyboard()
        )
        return DialogState.SET_PRODUCT_WEIGHT

    async def start_new_product_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления нового продукта в базу"""
        await send_card(
            update,
            context,
            title="Ввод продукта",
            fields=[("📛", "Пожалуйста, введите название продукта:")],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=Keyboards.get_cancel_keyboard()
        )
        return DialogState.SET_NEW_PRODUCT_CALORIES

    async def start_new_product_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ввод калорийности нового продукта"""
        product_name_input = update.message.text

        validation: ValidationResult = InputValidator.validate_product_name(product_name_input)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard())
            return DialogState.SET_NEW_PRODUCT_CALORIES

        context.user_data["product_name_input"] = product_name_input

        await send_card(
            update,
            context,
            title="Ввод калорийности",
            fields=[("🍽", "Пожалуйста, введите количество калорий на 100 г продукта:")],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=Keyboards.get_cancel_keyboard()
        )
        return DialogState.SAVE_NEW_PRODUCT

    async def save_new_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохранение нового продукта"""
        product_calories_input = update.message.text

        validation: ValidationResult = InputValidator.validate_calories(product_calories_input)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard())
            return DialogState.SAVE_NEW_PRODUCT

        await self.db.add_product(
            context.user_data["product_name_input"],
            int(product_calories_input)
        )

        await update.message.reply_text(
            "Успешно сохранено",
            reply_markup=Keyboards.get_main_keyboard()
        )
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена диалога"""
        await send_card(
            update,
            context,
            title="❌ Операция отменена",
            fields=[],
            footer="Выберите следующее действие ⬇️",
            keyboard=Keyboards.get_main_keyboard()
        )
        return ConversationHandler.END

    async def handle_cancel_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатия кнопки отмены"""
        return await self.cancel(update, context)

    def get_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler"""
        # Regex паттерн для кнопки отмены
        cancel_pattern = r"^(❌ Отмена|Отмена)$"

        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.TEXT & filters.Regex("^📅 Установить суточные калории$"),
                    self.start_calories_setup
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^➕ Добавить калории$"),
                    self.start_product_adding
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^🍗 Добавить продукт$"),
                    self.start_new_product_adding
                ),
            ],
            states={
                DialogState.SET_CALORIES: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_calories),
                ],
                DialogState.SET_PRODUCT_NAME: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_product_name),
                ],
                DialogState.SET_PRODUCT_WEIGHT: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_product_weight),
                ],
                DialogState.SET_TODAY_CALORIES: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_calories_for_today),
                ],
                DialogState.SET_NEW_PRODUCT_CALORIES: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.start_new_product_calories),
                ],
                DialogState.SAVE_NEW_PRODUCT: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_new_product),
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            allow_reentry=True
        )