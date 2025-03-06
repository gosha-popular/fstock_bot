import asyncio
import logging
from datetime import datetime

from icecream import ic


class SchedulerService:
    """
    Сервис для управления расписанием отправки сообщений
    / Service for managing message sending schedule
    """
    def __init__(self, func):
        """
        Инициализация сервиса расписания
        / Initialize the scheduler service
        
        Args:
            func: Функция, которая будет выполнятся
        """
        self.func = func
        self._day = None
        self._timesleep = 60
        self._running = False
        self._schedule_time = None
        self._schedule_day = None

    def set_scheduler(self, day=None, day_of_week=None, time_str=None):
        """
        Установка расписания отправки сообщений
        / Set message sending schedule
        
        Args:
            day: Число месяца, для выполнения
            day_of_week: День недели (0-6, где 0 - понедельник) / Day of week (0-6, where 0 is Monday)
            time_str: Время в формате "HH:MM" / Time in "HH:MM" format
            
        Raises:
            ValueError: Если формат времени неверный / If time format is invalid
        """

        if time_str:
            try:
                # Проверяем корректность формата времени / Check time format validity
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                raise ValueError("Неверный формат времени. Используйте формат HH:MM")

        self._day = day
        self._schedule_day = day_of_week
        self._schedule_time = time_str

        if not (day_of_week and time_str):
            self._timesleep = 60 * 60 * 24
        


    async def schedule_checker(self):
        """
        Проверка расписания и отправка сообщений в указанное время
        / Check schedule and send messages at specified time
        
        Работает в бесконечном цикле, проверяя текущее время каждую минуту
        / Runs in infinite loop, checking current time every minute
        """
        self._running = True
        while self._running:
            try:
                current_time = datetime.now()
                
                # Проверяем, нужно ли выполнить функцию / Check if run should be function
                should = True

                if self._day is not None:
                    should = should and current_time.day == self._day
                
                if self._schedule_day is not None:
                    should = should and current_time.weekday() == self._schedule_day
                
                if self._schedule_time is not None:
                    current_time_str = current_time.strftime("%H:%M")
                    should = should and current_time_str == self._schedule_time
                
                if should:
                    await self.func()
                
                # Ждем перед следующей проверкой / Wait before next check
                await asyncio.sleep(self._timesleep)
                
            except Exception as e:
                logging.error(f"Ошибка в schedule_checker: {e}", exc_info=True)
                await asyncio.sleep(60)  # В случае ошибки тоже ждем 1 минуту / Wait 1 minute in case of error too
