from db import Database

PRODUCTS_DB = {
    "Хлеб (пшеничный)": 265,
    "Хлеб (ржаной)": 210,
    "Молоко (2.5%)": 52,
    "Сыр твердый": 350,
    "Курица (филе)": 165,
    "Говядина": 250,
    "Свинина": 290,
    "Яйцо куриное": 155,
    "Картофель": 77,
    "Рис (сухой)": 330,
    "Гречка (сухая)": 310,
    "Овсянка (сухая)": 350,
    "Яблоко": 47,
    "Банан": 95,
    "Огурец": 15,
    "Помидор": 20,
    "Морковь": 41,
    "Сахар": 400,
    "Масло сливочное": 720,
    "Подсолнечное масло": 899,
}

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
    print("\n" + "=" * 50 + "\n")
    print("📋  Сводная таблица продуктов (ккал на 100г)".center(50) + "\n")
    print("=" * 50 + "\n")

    for i, (name, cal) in enumerate(products.items(), 1):
        print(f"{i:>2}. {name:<25} | {cal:>4} ккал " + "\n")

    print("=" * 50 + "\n" + "\n")

def init_product_table(db : Database):
    for p, (name, calories) in enumerate(PRODUCTS_DB.items(), 1):
        db.add_product(name, calories)
