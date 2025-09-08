import os
from contextvars import Context

from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from db import Database

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
db = Database()

start_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Начать")]],
    resize_keyboard=True)
main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Установить суточные калории")]]
)

# --- Обработка /start или любого первого сообщения
async def start(update: Update, context: CallbackContext):
    reply_markup = start_keyboard
    await update.message.reply_text("Приветствие", reply_markup=reply_markup)

async def handle_start_button(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        db.add_user(user_id)
        await update.message.reply_text("Добавил вас!", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Мы нашли ваши заметки!", reply_markup=main_keyboard)

async def handle_main_commands(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        await update.message.reply_text("Приступим к работе", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Не могу узнать вас...", reply_markup=start_keyboard)


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
        reply_markup=ReplyKeyboardRemove()
    )
    return SET_CALORIES

async def set_calories(update: Update, context: Context):
    """Обрабатывает ввод калорий"""
    user_id = update.effective_user.id
    try:
        calories = int(update.message.text)
        # Сохраняем калории в контексте или базе данных
        context.user_data['daily_calories'] = calories

        await update.message.reply_text(
            f"Установлено {calories} калорий в день!",
            reply_markup=main_keyboard
        )
        db.set_daily_calories(user_id, calories)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return SET_CALORIES


# Определяем состояния диалога
SET_CALORIES, ADD_PRODUCT = range(2)

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Bot is starting...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Начать" + "$"), handle_start_button))
    calories_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Установить суточные калории$"), start_calories_setup)],
        states={
            SET_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_calories)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(calories_conv_handler)
    app.run_polling()

if __name__ == "__main__":
    db.init_db()
    print("DB initialized...")
    main()