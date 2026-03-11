from log.log_writer import log
import pymorphy3

morph = pymorphy3.MorphAnalyzer(lang='ru')

def print_daily_report(products: list[tuple[str, int]]):
    total = sum(cal for _, cal in products)
    report = ""
    report += ("\n" + "=" * 40 + "\n")
    report +=("📊  Отчёт за сегодня".center(40) + "\n")
    report +=("=" * 40 + "\n")

    for i, (name, calories) in enumerate(products, 1):
        report += (f"{i:>2}. {name:<15} | {calories:>4} ккал" + "\n")

    report +=("-" * 40 + "\n")
    report +=(f"🔥  Всего калорий: {total} ккал".rjust(40) + "\n")
    report +=("=" * 40 + "\n")
    return report

def print_product_info( products: list[tuple[str,int]]):
    log('info',"\n" + "=" * 50 + "\n")
    log('info',"📋  Сводная таблица продуктов (ккал на 100г)".center(50) + "\n")
    log('info',"=" * 50 + "\n")

    for i, (name, cal) in enumerate(products.items(), 1):
        log('info',f"{i:>2}. {name:<25} | {cal:>4} ккал " + "\n")

    log('info',"=" * 50 + "\n" + "\n")

def get_lemma_word(word):
    return morph.parse(word)[0].normal_form

def multiply_calories(calories_per_hundred, product_weight):
    calories = (product_weight * calories_per_hundred) / 100
    return calories

async def send_card(update, context, title: str, fields: list[tuple[str, str]], footer: str = None, keyboard=None):
    """
       Универсальная функция для красивого форматирования сообщений в карточках.

       :param update: объект Update
       :param context: объект Context
       :param title: заголовок карточки (строка)
       :param fields: список пар (иконка/название поля, значение)
       :param footer: необязательная подпись под карточкой
       :param keyboard: reply_markup (например, main_keyboard)
       """

    lines = [f"📋 <b>{title}</b>", "━━━━━━━━━━━━━━━"]
    for label, value in fields:
        lines.append(f"{label} <b>{value}</b>")
    lines.append("━━━━━━━━━━━━━━━")

    if footer:
        lines.append(f"\n{footer}")

    message_text = "\n".join(lines)

    await update.message.reply_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
def print_help_info():
     return (
        "👋 <b>Привет!</b>\n"
        "Добро пожаловать в <b>Калькулятор Калорий 🍎</b>\n\n"
        "Выберите действие ниже, чтобы начать:\n\n"
        "📅 <b>Установить суточные калории</b> - устанавливает потолок калорий на день\n"
        "➕ <b>Добавить калории</b> - добавляйте количество калорий после приема пищи\n"
        "🔥 <b>Калории сегодня</b> - посмотреть сколько калорий было сегодня\n"
        "🧠 <b>Обучить модель</b> - (кнопка будет убрана позже)\n"
        "📸 <b>Распознать еду</b> - модель предположит продукт и его калорийность"
    )
