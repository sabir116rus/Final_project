# telegram_bot/run_bot.py

import os
import sys
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
import django

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')

# Инициализируем Django
django.setup()

# Создаём бота и диспетчер
from django.conf import settings
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Регистрация роутеров
router = Router()
dp.include_router(router)

# Обработчик команды /start
@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет, это бот для уведомлений о заказах!")

# Функция для запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
