import logging
import asyncio
from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from app.database.base import Session
from app.database.models import Channel

router = Router(name=__name__)


@router.my_chat_member()
async def handle_my_chat_member_update(event: ChatMemberUpdated):
    logging.info(f"Получено обновление my_chat_member: {event}")

    if event.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        try:
            session = Session()
            # Проверяем, не существует ли уже такой канал
            existing_channel = session.query(Channel).filter_by(channel_id=event.chat.id).first()
            if not existing_channel:
                channel = Channel(
                    channel_id=event.chat.id,
                    channel_title=event.chat.title
                )
                session.add(channel)
                session.commit()
                logging.info(f"Бот добавлен в канал: {event.chat.title}")
                
                # Ждем 1 секунду, чтобы права администратора успели примениться
                await asyncio.sleep(1)
                
                try:
                    # Отправляем сообщение через bot.send_message
                    await event.bot.send_message(
                        chat_id=event.chat.id,
                        text=f"Спасибо за добавление в канал {event.chat.title}! Теперь я буду отправлять сюда сообщения."
                    )
                except Exception as e:
                    logging.error(f"Ошибка при отправке сообщения в канал: {e}", exc_info=True)
            else:
                logging.info(f"Канал {event.chat.title} уже существует в базе данных")
        except Exception as e:
            logging.error(f"Ошибка при обработке обновления канала: {e}", exc_info=True)
        finally:
            session.close()
    else:
        logging.info(f"Получен статус {event.new_chat_member.status}, который не является ADMINISTRATOR")
