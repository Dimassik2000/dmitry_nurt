import pytest
from aiogram import Bot, Dispatcher
from aiogram import TestBot, TestDispatcher
from handlers import start

# Тестирование обработчика start
def test_handler_start():
    bot = TestBot(token="test")
    dispatcher = TestDispatcher(bot)
    dp = dispatcher.dp
    dp.register_message_handler(start.handle_start)
    result = dp.process_update(TestBot.get_message_update({"text": "/start"}))
    assert result["text"] == "Добро пожаловать! Начните, написав мне команду /help."

# Тестирование отправки сообщения ботом
def test_bot_send_message():
    bot = Bot(token="test")
    result = bot.send_message(chat_id=1234567890, text="Привет, мир!")
    assert result.message_id is not None

# Тестирование базы данных
@pytest.fixture(scope="module")
def test_database():
    return Database()

def test_check_user(test_database):
    user_id = 1234567890
    result = test_database.check_user(user_id)
    assert result is True