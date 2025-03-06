from aiogram import types, Router
from aiogram.filters import Command
from app.database.base import Session
from app.database.models import User
import logging

router = Router(name=__name__)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Сохранение пользователя в базу данных
    session = Session()
    try:
        # Проверяем, существует ли пользователь
        existing_user = session.query(User).filter_by(user_id=message.from_user.id).first()
        if not existing_user:
            user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(user)
            session.commit()
            await message.answer(f"Привет, {message.from_user.first_name}! Я бот для рассылки сообщений.")
        else:
            await message.answer(f"С возвращением, {message.from_user.first_name}! Я бот для рассылки сообщений.")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды start: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
    finally:
        session.close()