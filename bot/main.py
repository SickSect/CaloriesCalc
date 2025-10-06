import os
from contextvars import Context

from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from db import Database
from str_utils import print_daily_report, init_product_table, print_product_info

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
db = Database()

start_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Начать")]],
    resize_keyboard=True)
main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Установить суточные калории")],
        [KeyboardButton("Добавить калории")],
        [KeyboardButton("Калории сегодня")],
        [KeyboardButton("Добавить продукт и его калорийность")]
    ]
)
cancel_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Отмена")]
    ]
)

# Определяем состояния диалога
SET_CALORIES, ADD_PRODUCT, SET_TODAY_CALORIES, SET_PRODUCT_NAME = range(4)

# --- Обработка /start или любого первого сообщения
async def start(update: Update, context: CallbackContext):
    reply_markup = start_keyboard
    await update.message.reply_text("Приветствие", reply_markup=reply_markup)

async def get_main_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = start_keyboard
    await update.message.reply_text("", reply_markup=reply_markup)

async def handle_start_button(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        db.add_user(user_id)
        await update.message.reply_text("Добавил вас!", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Мы нашли ваши заметки!", reply_markup=main_keyboard)

async def handle_info_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    list = db.get_products_info()
    await update.message.reply_text(print_product_info(list), reply_markup=main_keyboard)

async def handle_today_calories(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        db.add_user(user_id)
        await update.message.reply_text("Добавил вас!", reply_markup=main_keyboard)
    else:
        report = db.get_today_calories(user_id)
        if report is not None:
            await update.message.reply_text( f"{print_daily_report(report)}", reply_markup=main_keyboard)
        elif report is None:
            await update.message.reply_text( "Сегодня калории не записаны", reply_markup=main_keyboard)
        else:
            await update.message.reply_text("Непредвиденная ошибка", reply_markup=main_keyboard)

async def cancel(update, context):
    """Отменяет диалог"""
    await update.message.reply_text(
        "Операция отменена",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

async def start_calories_setup(update, context):
    """Начинает процесс установки калорий"""
    await update.message.reply_text(
        "Пожалуйста, введите количество калорий:",
        reply_markup=cancel_keyboard
    )
    return SET_CALORIES

async def start_today_calories_setup(update, context):
    """Начинает процесс добавления калорий на сегодня"""
    await update.message.reply_text(
        "Пожалуйста, введите количество калорий:",
        reply_markup=cancel_keyboard
    )
    return SET_TODAY_CALORIES

async def start_product_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите название продукта:",
        reply_markup=cancel_keyboard
    )
    return

async def set_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод калорий"""
    user_id = update.effective_user.id
    text_input = update.message.text
    try:
        calories = int(text_input)
        db.set_daily_calories(user_id, calories)
        await update.message.reply_text(
            f"Установлено {calories} калорий в день!",
            reply_markup=main_keyboard
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:", reply_markup=cancel_keyboard)
        return SET_CALORIES

async def set_product_name(update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    try:
        if len(str(text_input)) > 60:
            raise ValueError("Название продукта не может быть длиннее 60 символов")
        context.user_data["product_name"] = text_input
        db.add_calories_for_today(update.effective_user.id, context.user_data["today_calories"],
                                  context.user_data["product_name"])
    except ValueError:
        await update.message.reply_text("Повторите ввод, вдруг ваше название длинее 60 символов",
                                        reply_markup=cancel_keyboard)

    return ConversationHandler.END

async def add_calories_for_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод калорий за сегодняшний день"""
    try:
        calories = int(update.message.text.strip())
        context.user_data["today_calories"] = calories
        await update.message.reply_text(
            "Пожалуйста, введите название продукта:"
        )
        return SET_PRODUCT_NAME
    except ValueError:
        await update.message.reply_text("Ошибка, повторите ввод:",
                                        reply_markup=cancel_keyboard)
        return SET_TODAY_CALORIES

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Bot is starting...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Начать" + "$"), handle_start_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Калории сегодня" + "$"), handle_today_calories))
    calories_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Установить суточные калории$"), start_calories_setup),
            MessageHandler(filters.TEXT & filters.Regex("^Добавить калории$"), start_today_calories_setup)],
            #MessageHandler(filters.TEXT & filters.Regex("^Калорийность продуктов$"), get_product_info)],
        states={
            SET_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_calories)],
            SET_TODAY_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_calories_for_today)],
            SET_PRODUCT_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, set_product_name)],
            #ADD_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_and_calories_per_hundread)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(calories_conv_handler)
    app.run_polling()

if __name__ == "__main__":
    db.init_db()
    print("DB initialized...")
    main()