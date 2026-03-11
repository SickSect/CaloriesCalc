import pytest

# Настройка для async тестов
pytest_plugins = ('pytest_asyncio',)

# Глобальная настройка asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test."
    )