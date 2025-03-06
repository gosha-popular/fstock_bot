import asyncio
import os
import subprocess
from datetime import datetime

import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.models import User, Channel
from app.handlers import router
from app.config import BOT_TOKEN
from app.services.scheduler import SchedulerService
from app.database.base import init_db, Session

import table

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def parse() -> str:
    subprocess.run(['python', 'table.py'])


admin = [804361300, ]


@dp.message(F.from_user.id.in_(admin), Command('send'))
async def get_bot_log(message: Message, command: CommandObject):
    if command.args == 'week':
        await send_report_to_week()
    elif command.args == 'month':
        await send_report_to_month()
    elif command.args == 'parse':
        await parse()
    else:
        await message.answer("I don't know this command")


async def on_startup():
    log_dir = Path('logs')
    if not log_dir.exists():
        log_dir.mkdir()

    # Создаем обработчик, который будет создавать новый файл лога каждый день
    handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'app'),
        when='D',  # 'midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    handler.suffix = "%Y-%m-%d_%H-%M-%S"
    handler.namer = lambda x: x + '.log'

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            handler, StreamHandler()
        ]
    )


async def send_report_to_week():
    result = f'<b>Еженедельный отчет.\nИндекс цен на продуктовую корзину на {datetime.now().strftime('%d.%m.%Y')}:</b>\n\n'
    result += table.get_text()

    await send_message_all_user_and_channel(result)


async def send_report_to_month():
    months = {
        1: "январь",
        2: "февраль",
        3: "март",
        4: "апрель",
        5: "май",
        6: "июнь",
        7: "июль",
        8: "август",
        9: "сентябрь",
        10: "октябрь",
        11: "ноябрь",
        12: "декабрь"
    }

    number = datetime.now().month - 1

    result = f'<b>Ежемесячный отчет.\nИндекс цен на продуктовую корзину на {months[number]} {datetime.now().year}:</b>\n\n'
    result += table.get_text_month(number)

    await send_message_all_user_and_channel(result)


async def send_message_all_user_and_channel(message: str):
    """
    Отправка сообщений всем пользователям и в активные каналы
    / Send messages to all users and active channels
    """
    session = Session()
    users = session.query(User).all()
    channels = session.query(Channel).filter(Channel.is_active == True).all()
    session.close()

    # Отправка сообщения пользователям / Send messages to users
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.user_id,
                text=message
            )
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения пользователю {user.user_id}: {e}")

    # Отправка сообщения в каналы / Send messages to channels
    for channel in channels:
        try:
            await bot.send_message(
                chat_id=channel.channel_id,
                text=message
            )
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения в канал {channel.channel_title}: {e}")
            # Если бот был удален из канала, деактивируем его
            # If bot was removed from channel, deactivate it
            if "bot was blocked by the user" in str(e):
                session = Session()
                channel.is_active = False
                session.commit()
                session.close()


async def main():
    """
    Основная функция запуска бота
    / Main function for bot startup
    
    Инициализирует базу данных, настраивает расписание и запускает бота
    / Initializes database, sets up schedule and starts the bot
    """
    # Настройка бота / Bot setup
    # Инициализация базы данных / Initialize database
    init_db()

    # Настройка сервиса расписания / Setup scheduler service
    scheduler = SchedulerService(send_report_to_month)
    scheduler.set_scheduler(day=1, time_str="10:00")

    parse_shed = SchedulerService(parse)
    parse_shed.set_scheduler(day_of_week=2, time_str='09:50')

    send_shed = SchedulerService(send_report_to_week)
    send_shed.set_scheduler(day_of_week=2, time_str='10:00')

    # Регистрация обработчиков / Register handlers

    dp.include_routers(router)

    # Запуск проверки расписания / Start schedule checker
    asyncio.create_task(scheduler.schedule_checker())
    asyncio.create_task(parse_shed.schedule_checker())
    asyncio.create_task(send_shed.schedule_checker())

    # Запуск бота с настройками для получения всех обновлений
    # Start bot with settings to receive all updates
    dp.startup.register(on_startup)
    await dp.start_polling(bot, allowed_updates=["chat_member", "message", "my_chat_member"])


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}")
