import config
import telebot

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("7758370360:AAFp9HPUkpszXrCHNj2PHG7uRZzGDbHfVeQ")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db") # Default to SQLite

#Админ ID - сюда нужно вставить свой telegram ID, чтобы можно было создавать комнаты
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
