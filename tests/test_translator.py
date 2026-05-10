from pathlib import Path

import pytest

from bot.translator import Translator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = PROJECT_ROOT / "locales"

@pytest.fixture
def translator():
    translator = Translator(str(LOCALES_DIR), "en")
    return translator


class TestTranslator:

    @pytest.mark.asyncio
    async def test_get_exist_key(self, translator):
        value = translator.get("start.title", "ru")
        assert value == "ℹ️ Справка"

    @pytest.mark.asyncio
    async def test_get_not_exist_key(self, translator):
        value = translator.get("start.titler", "ru")
        assert value == "start.titler"