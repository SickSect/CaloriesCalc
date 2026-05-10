import os
from pathlib import Path

from bot.translator import Translator
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

async def send_card(update, context,
                    title: str,
                    fields: list[tuple[str, str]],
                    footer: str = None, keyboard=None,
                    translator: Translator = None,):
    """
       Универсальная функция для красивого форматирования сообщений в карточках.

       :param update: объект Update
       :param context: объект Context
       :param title: заголовок карточки (строка)
       :param fields: список пар (иконка/название поля, значение)
       :param footer: необязательная подпись под карточкой
       :param keyboard: reply_markup (например, main_keyboard)
       """

    def safe_get(val):
        if val is None:
            return ""
        if translator is None:
            return str(val)
        return translator.get(val) if isinstance(val, str) else str(val)

    t_title = safe_get(title)
    t_fields = [
        (safe_get(label), safe_get(value))
        for label, value in fields
    ]
    t_footer = safe_get(footer)
    lines = [f"📋 <b>{t_title}</b>", "━━━━━━━━━━━━━━━"]
    for label, value in t_fields:
        lines.append(f"{label} <b>{value}</b>")
    lines.append("━━━━━━━━━━━━━━━")

    if t_footer:
        lines.append(f"\n{t_footer}")

    message_text = "\n".join(lines)

    await update.message.reply_text(
        message_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

def print_help_info():
    help_text = translator.get("help")
    return (help_text)
