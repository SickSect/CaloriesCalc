import asyncio
import logging
import os
from pathlib import Path

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
from bot.translator import Translator
from core.calculator import CalorieCalculator
from core.db import Database
from core.llm_service import LLMService
from core.str_utils import print_daily_report, send_card
from core.validator import InputValidator, ValidationResult

logger = logging.getLogger(__name__)



class BotHandlers:
    """Обработчики команд с внедрением зависимостей"""

    def __init__(self, db: Database, calculator: CalorieCalculator, llm: LLMService, translator: Translator):
        self.db = db
        self.calculator = calculator
        self.translator = translator
        self.llm = llm
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock(self, uid: int) -> asyncio.Lock:
        return self._locks.setdefault(uid, asyncio.Lock())

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        await send_card(
            update,
            context,
            title="start.title",
            fields=[
                ("📅", "start.fieldSetDailyCalories"),
                ("➕", "start.fieldAddCalories"),
                ("🔥", "start.fieldTodayCalories"),
                ("❓", "start.fieldAskAI")
            ],
            footer="start.footer",
            keyboard=Keyboards.get_start_keyboard(self.translator),
            translator=self.translator
        )

    async def handle_start_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Начать'"""
        async with self._lock(update.effective_user.id):
            user_id = update.effective_user.id
            if not await self.db.check_user_exists(user_id):
                await self.db.add_user(user_id)

            await send_card(
                update,
                context,
                title="handle_start_button.title",
                fields=[("👤", "handle_start_button.field")],
                footer="handle_start_button.footer",
                keyboard=Keyboards.get_main_keyboard(self.translator),
                translator=self.translator
            )


    async def handle_today_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр калорий за сегодня"""
        async with self._lock(update.effective_user.id):
            user_id = update.effective_user.id
            if not await self.db.check_user_exists(user_id):
                await self.db.add_user(user_id)

            report = await self.db.get_today_calories(user_id)
            limit = await self.db.get_daily_limit(user_id)

            if report:
                text = print_daily_report(report)
                if limit:
                    text += f"\n{self.translator.get('core.dailyLimit')} {limit} ccal"
                await update.message.reply_text(text, reply_markup=Keyboards.get_main_keyboard(self.translator))
            else:
                await update.message.reply_text(self.translator.get("error.caloriesNotFoundForToday"),
                                                reply_markup=Keyboards.get_main_keyboard(self.translator))

    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        async with self._lock(user_id):
            await send_card(
                update,
                context,
                title="handle_question.title",
                fields=[("🔥", "handle_question.field")],
                footer="handle_question.footer",
                keyboard=Keyboards.get_cancel_keyboard(self.translator),
                translator=self.translator
            )
            return DialogState.ASK_REQUEST

    async def start_calories_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало установки суточных калорий"""
        await send_card(
            update,
            context,
            title="start_calories_setup.title",
            fields=[("🔥", "start_calories_setup.field")],
            footer="start_calories_setup.footer",
            keyboard=Keyboards.get_cancel_keyboard(self.translator),
            translator=self.translator
        )
        return DialogState.SET_CALORIES

    async def set_llm_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        async with self._lock(user_id):
            text_input = update.message.text
            result = await self.llm.ask(text_input)
            await send_card(
                update,
                context,
                title="set_llm_request.title",
                fields=[("🔥", result)],
                footer="set_llm_request.footer",
                keyboard=Keyboards.get_main_keyboard(self.translator),
                translator=self.translator
            )
            return ConversationHandler.END

    async def set_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода суточных калорий"""
        user_id = update.effective_user.id

        async with self._lock(user_id):
            # ← ДОБАВЬ: создаём пользователя, если нет
            if not await self.db.check_user_exists(user_id):
                await self.db.add_user(user_id)

            text_input = update.message.text

            validation: ValidationResult = InputValidator.validate_calories(text_input, self.translator)

            if not validation.is_valid:
                await send_card(
                    update,
                    context,
                    title="set_calories.title_error",
                    fields=[("✏️", validation.error_message)],
                    footer="set_calories.footer_error",
                    keyboard=Keyboards.get_cancel_keyboard(self.translator),
                    translator=self.translator
                )
                return DialogState.SET_CALORIES

            calories = int(text_input)
            await self.db.set_daily_calories(user_id, calories)

            await send_card(
                update,
                context,
                title="set_calories.title",
                fields=[("🟢", "set_calories.field"), ("🔥", calories)],
                footer="set_calories.footer_error",
                keyboard=Keyboards.get_main_keyboard(self.translator),
                translator=self.translator
            )
            return ConversationHandler.END

    async def start_product_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления продукта"""
        await send_card(
            update,
            context,
            title="start_product_adding.title",
            fields=[("📛", "start_product_adding.field")],
            footer="start_product_adding.footer",
            keyboard=Keyboards.get_cancel_keyboard(self.translator),
            translator=self.translator
        )
        return DialogState.SET_PRODUCT_NAME

    async def set_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка названия продукта"""
        text_input = update.message.text.strip()
        user_id = update.effective_user.id
        async with self._lock(user_id):
            validation: ValidationResult = InputValidator.validate_product_name(text_input,self.translator)
            if not validation.is_valid:
                await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard(self.translator))
                return DialogState.SET_PRODUCT_NAME

            context.user_data["product_name"] = text_input

            if await self.db.check_product_exists(text_input):
                product_info = await self.db.get_product_info(text_input)
                await send_card(
                    update, context,
                    title="product.info.title",
                    fields=[
                        ("set_product_name.fieldNameLabel", product_info[2]),  # (иконка, ключ перевода, значение)
                        ("set_product_name.fieldCCalLabel", f"{product_info[1]} ccal / 100 g")
                    ],
                    footer="set_product_name.enter_weight",
                    keyboard=Keyboards.get_cancel_keyboard(self.translator),
                    translator=self.translator  # возьми из контекста: context.user_data.get("lang", "ru")
                )
                context.user_data["calories_per_hundred"] = product_info[1]
                return DialogState.SET_PRODUCT_WEIGHT
            else:
                await update.message.reply_text(
                    self.translator.get("error.productNotFound"),
                    reply_markup=Keyboards.get_cancel_keyboard(self.translator)
                )
                return DialogState.SET_TODAY_CALORIES

    async def set_product_weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка веса продукта"""
        text_input = update.message.text.strip()
        user_id = update.effective_user.id
        async with self._lock(user_id):
            validation: ValidationResult = InputValidator.validate_weight(text_input,self.translator)
            if not validation.is_valid:
                await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard(self.translator))
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
                title="set_product_weight.title",
                fields=[
                    ("set_product_weight.label_product", context.user_data["product_name"]),
                    ("set_product_weight.label_ccal", f"{calories}")
                ],
                footer="set_product_weight.footer",
                keyboard=Keyboards.get_main_keyboard(self.translator),
                translator=self.translator
            )
            return ConversationHandler.END

    async def add_calories_for_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода калорийности для нового продукта"""
        text_input = update.message.text.strip()
        user_id = update.effective_user.id
        async with self._lock(user_id):
            validation: ValidationResult = InputValidator.validate_calories(text_input,self.translator)
            if not validation.is_valid:
                await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard(self.translator))
                return DialogState.SET_TODAY_CALORIES

            calories = int(text_input)
            context.user_data["calories_per_hundred"] = calories

            # Добавляем продукт в базу
            await self.db.add_product(context.user_data["product_name"], calories)

            await send_card(
                update,
                context,
                title="add_calories_for_today.title",
                fields=[("⚖️", "add_calories_for_today.field")],
                footer="add_calories_for_today.footer",
                keyboard=Keyboards.get_cancel_keyboard(self.translator),
                translator=self.translator
            )
            return DialogState.SET_PRODUCT_WEIGHT

    async def start_new_product_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления нового продукта в базу"""
        await send_card(
            update,
            context,
            title="start_new_product_adding.title",
            fields=[("📛", "start_new_product_adding.field")],
            footer="start_new_product_adding.footer",
            keyboard=Keyboards.get_cancel_keyboard(self.translator),
            translator=self.translator
        )
        return DialogState.SET_NEW_PRODUCT_CALORIES

    async def start_new_product_calories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ввод калорийности нового продукта"""
        product_name_input = update.message.text

        validation: ValidationResult = InputValidator.validate_product_name(product_name_input,self.translator)
        if not validation.is_valid:
            await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard(self.translator))
            return DialogState.SET_NEW_PRODUCT_CALORIES

        context.user_data["product_name_input"] = product_name_input

        await send_card(
            update,
            context,
            title="start_new_product_calories.title",
            fields=[("🍽", "start_new_product_calories.field")],
            footer="start_new_product_calories.footer",
            keyboard=Keyboards.get_cancel_keyboard(self.translator),
            translator=self.translator
        )
        return DialogState.SAVE_NEW_PRODUCT

    async def save_new_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохранение нового продукта"""
        product_calories_input = update.message.text
        user_id = update.effective_user.id
        async with self._lock(user_id):
            validation: ValidationResult = InputValidator.validate_calories(product_calories_input,self.translator)
            if not validation.is_valid:
                await update.message.reply_text(validation.error_message, reply_markup=Keyboards.get_cancel_keyboard(self.translator))
                return DialogState.SAVE_NEW_PRODUCT

            await self.db.add_product(
                context.user_data["product_name_input"],
                int(product_calories_input)
            )

            await update.message.reply_text(
                self.translator.get("core.successSave"),
                reply_markup=Keyboards.get_main_keyboard(self.translator)
            )
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена диалога"""
        await send_card(
            update,
            context,
            title="cancel.title",
            fields=[],
            footer="cancel.footer",
            keyboard=Keyboards.get_main_keyboard(self.translator),
            translator=self.translator
        )
        return ConversationHandler.END

    async def handle_cancel_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатия кнопки отмены"""
        return await self.cancel(update, context)

    def get_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler"""
        # Regex паттерн для кнопки отмены
        cancel_pattern = self.translator.get("pattern.cancel")
        start_calories_setup_pattern = self.translator.get("pattern.set_daily_calories")
        start_product_adding_pattern = self.translator.get("pattern.start_product_adding")
        start_new_product_adding_pattern = self.translator.get("pattern.start_new_product_adding")
        handle_question_pattern = self.translator.get("pattern.handle_question")

        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.TEXT & filters.Regex(start_calories_setup_pattern),
                    self.start_calories_setup
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex(start_product_adding_pattern),
                    self.start_product_adding
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex(start_new_product_adding_pattern),
                    self.start_new_product_adding
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex(handle_question_pattern),
                    self.handle_question
                )
            ],
            states={
                DialogState.ASK_REQUEST: [
                    # ВАЖНО: Сначала отмена, потом основной хендлер!
                    MessageHandler(filters.Regex(cancel_pattern), self.handle_cancel_button),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_llm_request),
                ],
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