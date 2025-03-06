import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройки базы данных
DATABASE_URL = 'sqlite:///users.db'

# Настройки расписания
SCHEDULE_TIME = "10:26"