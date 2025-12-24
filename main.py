import logging
import os
from datetime import datetime
from multiprocessing import Process
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from bot.db import Database
from bot.str_utils import print_help_info, multiply_calories, send_card
from log.log_writer import log

from ml.dataset_collector import DataCollector
from ml.dataset_init import init_database, add_files_to_database
from ml.food_model import FoodModel
from ml.image_loader import download_train_data_for_classes, download_absent_data_for_classes, validate_images
from ml.data_loader import fill_list_on_init, DataLoader, get_json_config

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
db = Database()
fill_list_on_init()
food_model = FoodModel()
data_collector = DataCollector()
limit_downloaded_train_images = get_json_config("product_limit")
data_loader = DataLoader(limit_downloaded_train_images)
process_1_ended = False
process_2_ended = False

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
        [KeyboardButton("❌ Отмена")]
    ]
)

# Определяем состояния диалога
SET_CALORIES, ADD_PRODUCT, SET_PRODUCT_WEIGHT, SET_TODAY_CALORIES, SET_PRODUCT_CALORIES_PER_HUNDRED, SET_PRODUCT_NAME, PHOTO, SET_NEW_PRODUCT_CALORIES, SAVE_NEW_PRODUCT = range(9)

# --- Обработка /start или любого первого сообщения
async def start(update: Update, context: CallbackContext):
    reply_markup = start_keyboard
    await send_card(
        update,
        context,
        title="ℹ️ Справка",
        fields=[
            ("📅", "Установить суточные калории - устанавливает потолок калорий на день"),
            ("➕", "Добавить калории - добавляйте количество калорий после приема пищи"),
            ("🔥", "Калории сегодня - посмотреть сколько калорий было сегодня"),
            ("🧠", "Обучить модель - кнопка будет убрана позже"),
            ("📸", "Распознать еду - модель определит продукт и его калорийность")
        ],
        footer="Выберите действие ниже ⬇️",
        keyboard=reply_markup
    )

async def get_main_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = start_keyboard
    await update.message.reply_text("", reply_markup=reply_markup)

async def handle_start_button(update: Update,  context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.check_user_exists(user_id):
        db.add_user(user_id)
        await send_card(
            update,
            context,
            title="✅ Успешно",
            fields=[
                ("👤", "Добавил вас!")
            ],
            footer="Выберите следующее действие ⬇️",
            keyboard=main_keyboard
        )
    else:
        await send_card(
            update,
            context,
            title="📒 Ваши заметки",
            fields=[
                ("📝", "Мы нашли ваши заметки!")
            ],
            footer="Выберите следующее действие ⬇️",
            keyboard=main_keyboard
        )

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
            report = print_daily_report(report)
            limit = db.get_daily_limit(update.effective_user.id)
            if limit is not None:
                report = f"{report}\n{f'Ваш дневной лимит: {limit} калорий'}"
            await update.message.reply_text( f"{report}", reply_markup=main_keyboard)
        elif report is None:
            await update.message.reply_text( "Сегодня калории не записаны", reply_markup=main_keyboard)
        else:
            await update.message.reply_text("Непредвиденная ошибка", reply_markup=main_keyboard)

async def cancel(update, context):
    """Отменяет диалог"""
    await send_card(
        update,
        context,
        title="❌ Операция отменена",
        fields=[],
        footer="Выберите следующее действие ⬇️",
        keyboard=main_keyboard
    )
    return

async def start_calories_setup(update, context):
    """Начинает процесс установки калорий"""
    await send_card(
        update,
        context,
        title="Ввод калорий",
        fields=[
            ("🔥", "Пожалуйста, введите количество калорий:")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
    return SET_CALORIES

async def start_today_calories_setup(update, context):
    await send_card(
        update,
        context,
        title="Ввод продукта",
        fields=[
            ("📛", "Пожалуйста, введите название продукта:")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
    return SET_PRODUCT_NAME

async def start_new_product_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_card(
        update,
        context,
        title="Ввод продукта",
        fields=[
            ("📛", "Пожалуйста, введите название продукта:")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
    return SET_NEW_PRODUCT_CALORIES

async def start_new_product_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name_input = update.message.text
    context.user_data["product_name_input"] = product_name_input
    await send_card(
        update,
        context,
        title="Ввод калорийности",
        fields=[
            ("🍽", "Пожалуйста, введите количество калорий на 100 г продукта:")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
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

        await send_card(
            update,
            context,
            title="Цель установлена ✅",
            fields=[
                ("🔥", f"Установлено {calories} ккал в день")
            ],
            footer="Выберите следующее действие ⬇️",
            keyboard=main_keyboard
        )
        return ConversationHandler.END
    except ValueError:
        await send_card(
            update,
            context,
            title="Введите данные",
            fields=[
                ("✏️", "Пожалуйста, введите число:")
            ],
            footer="Для отмены используйте кнопку ниже ⬇️",
            keyboard=cancel_keyboard
        )
        return SET_CALORIES

async def set_calories_per_hundred(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calories_per_hundred_input = update.message.text.strip()
    context.user_data["today_calories"] = calories_per_hundred_input

    await send_card(
        update,
        context,
        title="Информация обновлена",
        fields=[
            ("🔥 Калорийность продукта:", f"{calories_per_hundred_input} ккал / 100 г"),
            ("🗓 Действие:", "добавлено в расписание калорий")
        ],
        footer="Выберите следующее действие ⬇️",
        keyboard=main_keyboard
    )
    db.add_calories_for_today(update.effective_user.id, calories_per_hundred_input, context.user_data["product_name"])
    return

async def set_product_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip()
    context.user_data["product_weight"] = text_input
    weight_calories = multiply_calories(float(context.user_data["calories_per_hundred"]), float(context.user_data["product_weight"]))
    db.add_calories_for_today(update.effective_user.id, weight_calories, context.user_data["product_name"])
    await send_card(update, context, title='Запись добавлена!', fields=[
        ("📛 Продукт:", context.user_data["product_name"]),
        ("🔥 Калорийность:", f"{weight_calories} ккал")
    ],
              footer='Выберите следующее действие', keyboard=main_keyboard)
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
            await update.message.reply_text(
                f"🥦 <b>Информация о продукте</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📛 <b>Название:</b> <i>{product_info[2]}</i>\n"
                f"🔥 <b>Калорийность:</b> <code>{product_info[1]} ккал / 100 г</code>\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Введите вес продукта в граммах ⬇️",
                parse_mode="HTML",
                reply_markup=cancel_keyboard
            )
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
    log('info', f"Добавлен продукт: {context.user_data['product_name']} : {context.user_data['calories_per_hundred']}")
    db.add_product(context.user_data["product_name"], context.user_data["calories_per_hundred"])
    await send_card(
        update,
        context,
        title="Ввод веса",
        fields=[
            ("⚖️", "Введите вес продукта:")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
    return SET_PRODUCT_WEIGHT


async def start_predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not food_model.is_trained:
        await send_card(
            update,
            context,
            title="⚠️ Модель не готова",
            fields=[
                ("❌", "Модель ещё не обучена!"),
                ("💡", "Сначала соберите данные и обучите модель.")
            ],
            footer="Выберите следующее действие ⬇️",
            keyboard=main_keyboard
        )
        return
    await send_card(
        update,
        context,
        title="Добавление фото 🍽",
        fields=[
            ("📸", "Пришлите фото еды для добавления в датасет")
        ],
        footer="Для отмены используйте кнопку ниже ⬇️",
        keyboard=cancel_keyboard
    )
    log('info',"Ожидание фото...")
    return PHOTO

async def predict_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предсказывает класс еды на фото"""
    if not process_1_ended and not process_2_ended:
        log('info', 'Процесс обучения невозможно начать, пока не закончится инициализация')
        await update.message.reply_text(
            f"❌ Процесс инициализация данных не завершен, для распознавания вернитесь позже",
            reply_markup=main_keyboard
        )
        return
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
async def train_model_command():
    """Обучает модель на собранных данных"""
    log('info', "🧠 Проверяем возможность обучения...")

    stats = data_collector.get_stats()

    if not stats['can_train']:
        response = (
            f"❌ Недостаточно данных для обучения!\n"
            f"📊 Собрано: {stats['trainable_samples']} фото\n"
            f"🎯 Нужно: минимум 20 фото\n\n"
            f"💡 Продолжайте отправлять фото еды с описаниями!"
        )
    else:
        log('info', "🎯 Начинаем обучение модели... Это займёт несколько минут.")

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
    log('info', response)

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

def model_train_process(exist_model, exist_dataset_db):
    if not exist_model:
        train_model_command()
    elif exist_model and len(data_loader.absent_list) > 0:
        file_path = os.path.join(os.path.dirname(__file__), "ml/trained_model.pth")
        os.remove(file_path)
        train_model_command()
    process_1_ended = True


def db_init_process(exist_model, exist_dataset_db):
    if not exist_model:
        validate_images()
    if len(data_loader.absent_list) > 0 and exist_dataset_db:
        new_files_dict = download_absent_data_for_classes(data_loader.absent_list)
        add_files_to_database(new_files_dict, data_collector)
    elif not exist_dataset_db:
        download_train_data_for_classes(limit_downloaded_train_images)
        init_database(data_collector)
    elif exist_dataset_db and count_rows_food_dataset['total_images'] == 0:
        init_database(data_collector)
    process_2_ended = True


if __name__ == "__main__":
    db.init_db()
    # Существует ли обученная модель
    exist_model = os.path.exists(os.path.join(os.path.dirname(__file__), "ml/trained_model.pth"))
    # Существует ли бд с данными
    exist_dataset_db = os.path.exists(os.path.join(os.path.dirname(__file__), "ml/food_dataset.db"))
    count_rows_food_dataset = data_collector.get_stats()

    p1 = Process(target=db_init_process, args=(exist_model, exist_dataset_db))
    p2 = Process(target=model_train_process, args=(exist_model, exist_dataset_db))

    p1.start()
    p2.start()
    main()

