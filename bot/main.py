import os
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.handlers import BotHandlers
from bot.translator import Translator
from core.calculator import CalorieCalculator
from core.db import Database
from core.llm_service import LLMService
from log.log_writer import log

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def post_init(application):
    await application.bot_data["db"].connect()
    log('info', "[DB] connected")
    await application.bot_data["llm"].initialization()
    log('info', "[LLM] connected")

async def post_shutdown(application):
    await application.bot_data["db"].disconnect()
    log('info', "[DB] disconnected")


def create_application() -> tuple:
    db = Database()
    calculator = CalorieCalculator()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    llm = LLMService(url, model, 60)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    LOCALES_DIR = PROJECT_ROOT / str(os.getenv("LOCALES_DIR"))
    default_lang = os.getenv('LANGUAGE')
    translator = Translator(str(LOCALES_DIR), default_lang)

    app.bot_data["db"] = db
    app.bot_data["llm"] = llm
    app.bot_data["translator"] = translator

    handlers = BotHandlers(db, calculator, llm, translator)
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(translator.get("pattern.start")),
        handlers.handle_start_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(translator.get("pattern.todayCalories")),
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
