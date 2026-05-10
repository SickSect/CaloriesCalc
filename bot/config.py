import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    # DB
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    # LLM
    LLM_DEVICE = os.environ.get("LLM_DEVICE")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
    LLM_MODEL = os.environ.get("LLM_MODEL")
    # CACHE
    REDIS_URL = os.environ.get("REDIS_URL")
    CACHE_TTL = os.environ.get("CACHE_TTL")
    # BOT
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    LOG_LEVEL = os.environ.get("LOG_LEVEL")

