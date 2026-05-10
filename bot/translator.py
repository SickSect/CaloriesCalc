import json
from pathlib import Path

from log.log_writer import log


class Translator:
    def __init__(self, locales_dir: str="locales", default_lang: str="en"):
        log("info", "Default lang:" + default_lang)
        log("info", "Locales dir: " + locales_dir)
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self.cache: dict = {}

    def load(self, lang: str) -> dict:
        if lang not in self.cache:
            path = Path(self.locales_dir) / f"{lang}.json"
            self.cache[lang] = json.loads(path.read_text("utf-8")) if path.exists() else {}
        return self.cache[lang]

    def get(self, key: str, lang: str = None, **kwargs) -> str:
        if not isinstance(key, str):
            return str(key)

        lang = lang or self.default_lang
        data = self.load(lang)
        # Простой поиск по точкам: "start.title" → data["start"]["title"]
        value = data
        for part in key.split("."):
            value = value.get(part, {}) if isinstance(value, dict) else {}
        result = value if isinstance(value, str) else key  # Fallback на ключ, если не нашли

        # Подстановка переменных: "Привет, {name}" → "Привет, Иван"
        if kwargs:
            result = result.format(**kwargs)
        return result
