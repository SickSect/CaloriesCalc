import os
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from bot.db import Database

from ml.dataset_collector import DataCollector
from ml.dataset_init import init_database
from ml.food_model import FoodModel
from ml.image_loader import download_train_data_for_classes, download_absent_data_for_classes
from ml.product_lists import fill_list_on_init, DataLoader

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
db = Database()
food_model = FoodModel()
data_collector = DataCollector()
limit_downloaded_train_images = 50
data_loader = DataLoader(limit_downloaded_train_images)

start_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Начать")]],
    resize_keyboard=True)
main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Установить суточные калории")],
        [KeyboardButton("Добавить калории")],
        [KeyboardButton("Калории сегодня")],
        [KeyboardButton("Добавить продукт и его калорийность")],
        [KeyboardButton("Обучить модель")],
        [KeyboardButton("Распознать еду")]
    ]
)
cancel_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Отмена")]
    ]
)

# Определяем состояния диалога
SET_CALORIES, ADD_PRODUCT, SET_TODAY_CALORIES, SET_PRODUCT_NAME, PHOTO = range(5)

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
    from bot.str_utils import print_product_info
    await update.message.reply_text(print_product_info(list), reply_markup=main_keyboard)

async def handle_today_calories(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        db.add_user(user_id)
        await update.message.reply_text("Добавил вас!", reply_markup=main_keyboard)
    else:
        report = db.get_today_calories(user_id)
        if report is not None:
            from bot.str_utils import print_daily_report
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

async def start_predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not food_model.is_trained:
        await update.message.reply_text(
            "❌ Модель ещё не обучена!\n"
            "💡 Сначала соберите данные и обучите модель.",
            reply_markup=main_keyboard
        )
        return
    await update.message.reply_text("📸 Пришлите фото еды для добавления в датасет")
    print("Ожидание фото...")
    return PHOTO

async def predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предсказывает класс еды на фото"""
    print("Получили фото. Начинается распознавание...")
    try:
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Создаем временный файл
        temp_path = f"temp_{user_id}_{datetime.now().strftime('%H%M%S')}.jpg"
        await file.download_to_drive(temp_path)

        # Предсказываем
        result = food_model.predict(temp_path)

        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if result['success']:
            response = (
                f"🎯 Результат распознавания:\n"
                f"• Класс: {result['food_class']}\n"
                f"• Уверенность: {result['confidence']}%\n"
                f"• {result['message']}"
            )

            # Показываем все вероятности
            if 'all_probabilities' in result:
                response += "\n\n📊 Все вероятности:\n"
                for cls, prob in result['all_probabilities'].items():
                    response += f"• {cls}: {prob}%\n"
        else:
            response = f"❌ Ошибка: {result['error']}"

        await update.message.reply_text(response, reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при распознавании: {str(e)}",
            reply_markup=main_keyboard
        )
        return ConversationHandler.END


# Добавляем команду для обучения модели
async def train_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обучает модель на собранных данных"""
    await update.message.reply_text("🧠 Проверяем возможность обучения...")

    stats = data_collector.get_stats()

    if not stats['can_train']:
        response = (
            f"❌ Недостаточно данных для обучения!\n"
            f"📊 Собрано: {stats['trainable_samples']} фото\n"
            f"🎯 Нужно: минимум 20 фото\n\n"
            f"💡 Продолжайте отправлять фото еды с описаниями!"
        )
    else:
        await update.message.reply_text("🎯 Начинаем обучение модели... Это займёт несколько минут.")

        # Обучаем модель
        success = food_model.train(data_collector, epochs=25)

        if success:
            response = (
                f"✅ Модель успешно обучена!\n"
                f"📊 Обучено на: {stats['trainable_samples']} фото\n"
                f"🎯 Теперь я могу распознавать еду на фото!\n\n"
                f"📈 Статистика по классам:\n"
            )

            for cls, count in stats['by_class'].items():
                response += f"• {cls}: {count} фото\n"
        else:
            response = "❌ Не удалось обучить модель. Попробуйте позже."

    await update.message.reply_text(response, reply_markup=main_keyboard)


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет фото еды для обучения модели"""
    try:
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        caption = update.message.caption or "Фото еды"

        # Скачиваем фото
        image_bytes = await file.download_as_bytearray()

        # Сохраняем в датасет
        filename, predicted_class = data_collector.save_food_image(
            bytes(image_bytes), caption, user_id
        )

        # Статистика
        stats = data_collector.get_stats()

        response = (
            f"📸 Фото сохранено в датасет!\n"
            f"📝 Описание: '{caption}'\n"
            f"🏷 Авто-разметка: {predicted_class}\n"
            f"📊 Всего собрано: {stats['total_images']} фото\n"
            f"🎯 Готово для обучения: {stats['trainable_samples']} фото"
        )

        if stats['can_train'] and not food_model.is_trained:
            response += "\n\n✅ Достаточно данных для обучения модели!"

        await update.message.reply_text(response, reply_markup=main_keyboard)

    except Exception as e:
        print(f"❌ Ошибка сохранения фото: {e}")
        await update.message.reply_text(
            "❌ Не удалось сохранить фото. Попробуйте ещё раз.",
            reply_markup=main_keyboard
        )

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Bot is starting...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Начать" + "$"), handle_start_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Калории сегодня" + "$"), handle_today_calories))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Обучить модель" + "$"), train_model_command))
    calories_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Установить суточные калории$"), start_calories_setup),
            MessageHandler(filters.TEXT & filters.Regex("^Добавить калории$"), start_today_calories_setup),
            MessageHandler(filters.TEXT & filters.Regex("^" + "Распознать еду" + "$"), start_predict_food)],
        states={
            SET_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_calories)],
            SET_TODAY_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_calories_for_today)],
            SET_PRODUCT_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, set_product_name)],
            PHOTO: [MessageHandler(filters.PHOTO, predict_food)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(calories_conv_handler)
    app.run_polling()

if __name__ == "__main__":
    db.init_db()
    if data_loader.absent_list:
        new_files_dict = download_absent_data_for_classes(data_loader.absent_list)
    else:
        download_train_data_for_classes(limit_downloaded_train_images)
        init_database(data_collector)
    main()