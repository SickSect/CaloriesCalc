import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers import BotHandlers
from bot.states import DialogState
from core.calculator import CalorieCalculator
from core.db import Database


# ===== ФИКСТУРЫ =====

@pytest.fixture(scope="function")
def test_db():
    """Тестовая БД во временном файле"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_path = temp_file.name
    temp_file.close()

    db = Database(temp_path)
    db.init_db(skip_init_data=True)

    yield db

    # Очистка
    if hasattr(db, 'close'):
        db.close()

    import gc
    gc.collect()

    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except PermissionError:
        pass


@pytest.fixture
def calculator():
    """Калькулятор калорий"""
    return CalorieCalculator()


@pytest.fixture
def handlers(test_db, calculator):
    """Создание хендлеров с тестовыми зависимостями"""
    return BotHandlers(test_db, calculator)


@pytest.fixture
def mock_update():
    """
    Фикстура: фейковое сообщение Telegram.
    Имитирует реальный Update от Telegram API.
    """
    update = MagicMock(spec=Update)
    update.message = MagicMock()
    update.message.text = "2000"
    update.message.reply_text = AsyncMock()  # ← Асинхронный мок
    update.message.edit_text = AsyncMock()
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"
    return update


@pytest.fixture
def mock_context():
    """
    Фикстура: фейковый контекст.
    Хранит user_data между шагами диалога.
    """
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context
# ===== ТЕСТЫ =====

class TestBotHandlers:
    """Тесты на обработчики команд бота"""

    # ----- Тест команды /start -----

    @pytest.mark.asyncio
    async def test_start_command(self, handlers, mock_update, mock_context):
        """Тест команды /start"""
        await handlers.start(mock_update, mock_context)

        # Проверяем, что был вызван reply_text
        assert mock_update.message.reply_text.called

        # Проверяем, что вызван хотя бы 1 раз
        assert mock_update.message.reply_text.call_count >= 1

    # ----- Тест кнопки 'Начать' -----

    @pytest.mark.asyncio
    async def test_handle_start_button_new_user(self, handlers, mock_update, mock_context):
        """Тест кнопки 'Начать' для нового пользователя"""
        # Пользователя нет в БД
        assert handlers.db.check_user_exists(12345) == False

        await handlers.handle_start_button(mock_update, mock_context)

        # Пользователь добавлен в БД
        assert handlers.db.check_user_exists(12345) == True

        # Ответ отправлен
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_handle_start_button_existing_user(self, handlers, mock_update, mock_context):
        """Тест кнопки 'Начать' для существующего пользователя"""
        # Сначала добавляем пользователя
        handlers.db.add_user(12345)

        await handlers.handle_start_button(mock_update, mock_context)

        # Ответ отправлен
        assert mock_update.message.reply_text.called

    # ----- Тест установки калорий -----

    @pytest.mark.asyncio
    async def test_set_calories_valid_input(self, handlers, mock_update, mock_context):
        """Тест ввода валидных калорий"""
        mock_update.message.text = "2500"

        result = await handlers.set_calories(mock_update, mock_context)

        # Диалог завершен
        assert result == ConversationHandler.END

        # Лимит установлен в БД
        limit = handlers.db.get_daily_limit(12345)
        assert limit == 2500

        # Ответ отправлен
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_set_calories_invalid_input(self, handlers, mock_update, mock_context):
        """Тест ввода невалидных калорий (текст вместо числа)"""
        mock_update.message.text = "abc"

        result = await handlers.set_calories(mock_update, mock_context)

        # Диалог продолжается (ждем корректный ввод)
        assert result == DialogState.SET_CALORIES

        # Лимит НЕ установлен
        limit = handlers.db.get_daily_limit(12345)
        assert limit is None

        # Ответ об ошибке отправлен
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_set_calories_negative_value(self, handlers, mock_update, mock_context):
        """Тест ввода отрицательных калорий"""
        mock_update.message.text = "-500"

        result = await handlers.set_calories(mock_update, mock_context)

        # Диалог продолжается (ошибка валидации)
        assert result == DialogState.SET_CALORIES

    @pytest.mark.asyncio
    async def test_set_calories_too_large(self, handlers, mock_update, mock_context):
        """Тест ввода слишком большого значения"""
        mock_update.message.text = "999999"

        result = await handlers.set_calories(mock_update, mock_context)

        # Диалог продолжается (ошибка валидации)
        assert result == DialogState.SET_CALORIES

    # ----- Тест отмены диалога -----

    @pytest.mark.asyncio
    async def test_cancel_handler(self, handlers, mock_update, mock_context):
        """Тест отмены диалога через /cancel"""
        result = await handlers.cancel(mock_update, mock_context)

        # Диалог завершен
        assert result == ConversationHandler.END

        # Ответ отправлен
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_handle_cancel_button(self, handlers, mock_update, mock_context):
        """Тест кнопки отмены '❌ Отмена'"""
        mock_update.message.text = "❌ Отмена"

        result = await handlers.handle_cancel_button(mock_update, mock_context)

        # Диалог завершен
        assert result == ConversationHandler.END

    # ----- Тест добавления продукта -----

    @pytest.mark.asyncio
    async def test_set_product_weight(self, handlers, mock_update, mock_context):
        """Тест расчета веса продукта"""
        # Подготовка данных
        handlers.db.add_user(12345)
        handlers.db.add_product("Яблоко", 52)

        mock_context.user_data["product_name"] = "Яблоко"
        mock_context.user_data["calories_per_hundred"] = 52
        mock_update.message.text = "150"  # 150 грамм

        result = await handlers.set_product_weight(mock_update, mock_context)

        # Диалог завершен
        assert result == ConversationHandler.END

        # Калории добавлены в БД
        report = handlers.db.get_today_calories(12345)
        assert report is not None

        # Проверка расчета: 52 * 150 / 100 = 78 ккал
        assert report[0][1] == 78.0

    @pytest.mark.asyncio
    async def test_set_product_weight_invalid(self, handlers, mock_update, mock_context):
        """Тест невалидного веса"""
        mock_context.user_data["product_name"] = "Яблоко"
        mock_context.user_data["calories_per_hundred"] = 52
        mock_update.message.text = "abc"

        result = await handlers.set_product_weight(mock_update, mock_context)

        # Диалог продолжается
        assert result == DialogState.SET_PRODUCT_WEIGHT

    @pytest.mark.asyncio
    async def test_set_product_weight_zero(self, handlers, mock_update, mock_context):
        """Тест веса = 0"""
        mock_context.user_data["product_name"] = "Яблоко"
        mock_context.user_data["calories_per_hundred"] = 52
        mock_update.message.text = "0"

        result = await handlers.set_product_weight(mock_update, mock_context)

        # Диалог продолжается (ошибка валидации)
        assert result == DialogState.SET_PRODUCT_WEIGHT

    # ----- Тест добавления нового продукта -----

    @pytest.mark.asyncio
    async def test_save_new_product(self, handlers, mock_update, mock_context):
        """Тест сохранения нового продукта"""
        mock_context.user_data["product_name_input"] = "Авокадо"
        mock_update.message.text = "160"

        result = await handlers.save_new_product(mock_update, mock_context)

        # Диалог завершен
        assert result == ConversationHandler.END

        # Продукт добавлен в БД
        assert handlers.db.check_product_exists("Авокадо") == True

        # Ответ отправлен
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_save_new_product_invalid_calories(self, handlers, mock_update, mock_context):
        """Тест невалидных калорий при сохранении продукта"""
        mock_context.user_data["product_name_input"] = "Авокадо"
        mock_update.message.text = "abc"

        result = await handlers.save_new_product(mock_update, mock_context)

        # Диалог продолжается
        assert result == DialogState.SAVE_NEW_PRODUCT

    # ----- Тест названия продукта -----

    @pytest.mark.asyncio
    async def test_set_product_name_existing(self, handlers, mock_update, mock_context):
        """Тест ввода существующего продукта"""
        handlers.db.add_user(12345)
        handlers.db.add_product("Гречка", 343)

        mock_update.message.text = "Гречка"

        result = await handlers.set_product_name(mock_update, mock_context)

        # Переход к вводу веса
        assert result == DialogState.SET_PRODUCT_WEIGHT

        # Данные сохранены в контекст
        assert mock_context.user_data["product_name"] == "Гречка"
        assert mock_context.user_data["calories_per_hundred"] == 343

    @pytest.mark.asyncio
    async def test_set_product_name_not_existing(self, handlers, mock_update, mock_context):
        """Тест ввода несуществующего продукта"""
        handlers.db.add_user(12345)

        mock_update.message.text = "Неизвестный продукт"

        result = await handlers.set_product_name(mock_update, mock_context)

        # Переход к вводу калорийности
        assert result == DialogState.SET_TODAY_CALORIES

    @pytest.mark.asyncio
    async def test_set_product_name_too_long(self, handlers, mock_update, mock_context):
        """Тест слишком длинного названия"""
        mock_update.message.text = "А" * 100

        result = await handlers.set_product_name(mock_update, mock_context)

        # Диалог продолжается (ошибка валидации)
        assert result == DialogState.SET_PRODUCT_NAME