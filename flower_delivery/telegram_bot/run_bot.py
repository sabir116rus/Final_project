# telegram_bot/run_bot.py

import os
import sys
import asyncio
import django

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Устанавливаем переменную окружения с настройками Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')

# Инициализируем Django
django.setup()

from telegram_bot.bot import bot, dp

async def main():
    try:
        # Запускаем поллинг бота
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
