# telegram_bot/bot.py

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings
from telegram_bot.handlers import register_handlers

# Инициализируем бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Создаем хранилище для FSM (можно использовать другое, например Redis)
storage = MemoryStorage()

# Инициализируем диспетчер
dp = Dispatcher(storage=storage)

# Регистрируем обработчики
dp.include_router(register_handlers())
