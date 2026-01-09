import os
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ContextTypes, \
    ConversationHandler
from bot.db import Database
from bot.str_utils import print_help_info, multiply_calories
from log.log_writer import log
from ml.dataset_collector import DataCollector
from ml.loader.data_loader import fill_list_on_init, DataLoader, get_json_config
from ml.loader.image_downloader import download_data_to_folder
from ml.model.food_model import FoodNet

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
db = Database()
fill_list_on_init()
food_model = FoodNet()
data_collector = DataCollector()
limit_downloaded_train_images = get_json_config("train_product_limit")
limit_downloaded_test_images = get_json_config("test_product_limit")
data_loader = DataLoader(limit_downloaded_train_images, limit_downloaded_test_images)

start_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Начать")]],
    resize_keyboard=True)
main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📅 Установить суточные калории")],
        [KeyboardButton("➕ Добавить калории")],
        [KeyboardButton("🔥 Калории сегодня")],
        [KeyboardButton("🍗 Добавить продукт")],
        #[KeyboardButton("🧠 Обучить модель")],
        [KeyboardButton("📸 Распознать еду")]
    ]
)
cancel_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Отмена")]
    ]
)

# Определяем состояния диалога
SET_CALORIES, ADD_PRODUCT, SET_PRODUCT_WEIGHT, SET_TODAY_CALORIES, SET_PRODUCT_CALORIES_PER_HUNDRED, SET_PRODUCT_NAME, PHOTO, SET_NEW_PRODUCT_CALORIES, SAVE_NEW_PRODUCT = range(9)

# --- Обработка /start или любого первого сообщения
async def start(update: Update, context: CallbackContext):
    reply_markup = start_keyboard
    await update.message.reply_text(print_help_info(), reply_markup=reply_markup)

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
    return

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
        "Пожалуйста, введите название продукта:",
        reply_markup=cancel_keyboard
    )
    return SET_PRODUCT_NAME

async def start_product_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите название продукта:",
        reply_markup=cancel_keyboard
    )
    return SET_PRODUCT_NAME

async def start_new_product_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите название продукта:",
        reply_markup=cancel_keyboard
    )
    return SET_NEW_PRODUCT_CALORIES

async def start_new_product_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name_input = update.message.text
    context.user_data["product_name_input"] = product_name_input
    await update.message.reply_text(
        "Пожалуйста, введите количество калорий на 100 грамм продукта:",
        reply_markup=cancel_keyboard)
    return SAVE_NEW_PRODUCT

async def save_new_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_calories_input = update.message.text
    context.user_data["product_calories_input"] = product_calories_input
    db.add_product(context.user_data["product_name_input"], context.user_data["product_calories_input"])
    await update.message.reply_text(
        "Успешно сохранено",
        reply_markup=main_keyboard)
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

async def set_calories_per_hundred(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calories_per_hundred_input = update.message.text.strip()
    context.user_data["today_calories"] = calories_per_hundred_input
    await update.message.reply_text(f"Калорийность указанного продукта: {calories_per_hundred_input}, мы добавили это в расписание калорий")
    db.add_calories_for_today(update.effective_user.id, calories_per_hundred_input, context.user_data["product_name"])
    return

async def set_product_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    context.user_data["product_weight"] = text_input
    weight_calories = multiply_calories(float(context.user_data["calories_per_hundred"]), float(context.user_data["product_weight"]))
    db.add_calories_for_today(update.effective_user.id, weight_calories, context.user_data["product_name"])
    await update.message.reply_text(f"Добавлена запись:\n калорийность {weight_calories} продукта {context.user_data['product_name']}",
                                    reply_markup=main_keyboard)
    return

async def set_product_name(update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    try:
        if len(str(text_input)) > 60:
            raise ValueError("Название продукта не может быть длиннее 60 символов")
            return
        context.user_data["product_name"] = text_input
        await update.message.reply_text("Поиск продукта в заметках...",
                                        reply_markup=cancel_keyboard)
        if db.check_product_exists(text_input):
            product_info = db.get_product_info(text_input)
            await update.message.reply_text(f"Найден продукт: {product_info[2]} с калорийностью {product_info[1]}\n\nВведите вес продукта в граммах:",
                                            reply_markup=cancel_keyboard)
            context.user_data["calories_per_hundred"] = product_info[1]
            return SET_PRODUCT_WEIGHT
        else:
            await update.message.reply_text(f"Продукт не найден. Введите его калорийность на 100 грамм:",
                                            reply_markup=cancel_keyboard)
            return SET_TODAY_CALORIES
    except ValueError:
        await update.message.reply_text("Повторите ввод, вдруг ваше название длиннее 60 символов",
                                        reply_markup=cancel_keyboard)
        return


async def add_calories_for_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод калорий за сегодняшний день"""
    product_calories_per_hundred = update.message.text.strip()
    context.user_data["calories_per_hundred"] = product_calories_per_hundred
    await update.message.reply_text(f"Введите вес продукта:",
                                    reply_markup=cancel_keyboard)
    return SET_PRODUCT_WEIGHT


async def start_predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not food_model.is_trained:
        await update.message.reply_text(
            "❌ Модель ещё не обучена!\n"
            "💡 Сначала соберите данные и обучите модель.",
            reply_markup=main_keyboard
        )
        return
    await update.message.reply_text("📸 Пришлите фото еды для добавления в датасет")
    log('info',"Ожидание фото...")
    return PHOTO

async def predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предсказывает класс еды на фото"""
    log('info',"Получили фото. Начинается распознавание...")
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
        success = food_model.train(data_collector, epochs=10)

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
        predicted_class = data_collector.save_food_image(
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
        log('info', f"❌ Ошибка сохранения фото: {e}")
        await update.message.reply_text(
            "❌ Не удалось сохранить фото. Попробуйте ещё раз.",
            reply_markup=main_keyboard
        )

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    log('info',"Bot is starting...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Начать" + "$"), handle_start_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "🔥 Калории сегодня" + "$"), handle_today_calories))
    #app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^" + "Обучить модель" + "$"), train_model_command))
    calories_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^📅 Установить суточные калории$"), start_calories_setup),
            MessageHandler(filters.TEXT & filters.Regex("^➕ Добавить калории$"), start_today_calories_setup),
            MessageHandler(filters.TEXT & filters.Regex("^📸 Распознать еду$"), start_predict_food),
            MessageHandler(filters.TEXT & filters.Regex("^🍗 Добавить продукт$"), start_new_product_adding)],
        states={
            SET_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_calories)],
            SET_TODAY_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_calories_for_today)],
            SET_PRODUCT_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, set_product_name)],
            SET_PRODUCT_CALORIES_PER_HUNDRED: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_calories_per_hundred)],
            SET_NEW_PRODUCT_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_new_product_calories)],
            SAVE_NEW_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_product)],
            SET_PRODUCT_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_product_weight)],
            PHOTO: [MessageHandler(filters.PHOTO, predict_food)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    app.add_handler(calories_conv_handler)
    app.run_polling()

if __name__ == "__main__":
    # init db
    # Download
    print('LEN TRAIN:', len(data_loader.trains_absent_list))
    print('KEYS TRAIN:', data_loader.trains_absent_list.keys())
    print('LEN TEST', len(data_loader.test_absent_list))
    print('KEYS TEST:', data_loader.test_absent_list.keys())
    exist_dataset_db = os.path.exists(os.path.join(os.path.dirname(__file__), "ml/food_dataset.db"))
    if len(data_loader.trains_absent_list) > 0 and exist_dataset_db:
       new_files_dict = download_data_to_folder(data_loader.trains_absent_list, 'train_images')

    if len(data_loader.test_absent_list) > 0 and exist_dataset_db:
       new_files_dict = download_data_to_folder(data_loader.test_absent_list, 'test_images')


    #if exist_model:
    #    validate_images_by_folder('test_images')
    #    validate_images_by_folder('train_images')
    #if len(data_loader.trains_absent_list) > 0 and exist_dataset_db:
    #    new_files_dict = download_absent_data_for_classes(data_loader.trains_absent_list, 'train_images')
    #    add_files_to_database(new_files_dict, data_collector, True)
    #if len(data_loader.test_absent_list) > 0 and exist_dataset_db:
    #    new_files_dict = download_absent_data_for_classes(data_loader.trains_absent_list, 'test_images')
    #    add_files_to_database(new_files_dict, data_collector, False)
    #if not exist_dataset_db:
    #    download_absent_data_for_classes(limit_downloaded_train_images, 'train_images')
    #    download_absent_data_for_classes(limit_downloaded_test_images, 'test_images')
    #    init_database(data_collector)
    #main()