import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.handlers import BotHandlers
from core.calculator import CalorieCalculator
from core.db import Database
from log.log_writer import log

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def post_init(application):
    await application.bot_data["db"].connect()
    log('info', "[DB] connected")


async def post_shutdown(application):
    await application.bot_data["db"].disconnect()
    log('info', "[DB] disconnected")


def create_application() -> tuple:
    db = Database()
    calculator = CalorieCalculator()
    handlers = BotHandlers(db, calculator)

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.bot_data["db"] = db

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Начать$"),
        handlers.handle_start_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔥 Калории сегодня$"),
        handlers.handle_today_calories
    ))
    app.add_handler(handlers.get_conversation_handler())

    return app, handlers


def main():
    """Точка входа"""
    log('info', "Bot is starting...")
    app, _ = create_application()
    app.run_polling()


if __name__ == "__main__":
    main()
