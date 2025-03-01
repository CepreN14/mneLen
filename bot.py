from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import requests

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL вашего API
API_URL = "http://127.0.0.1:5000"

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Добро пожаловать в чат! Используйте /newroom для создания комнаты.")

# Команда /newroom
async def new_room(update: Update, context: CallbackContext) -> None:
    room_name = " ".join(context.args)
    if room_name:
        # Отправляем данные на API
        response = requests.post(
            f"{API_URL}/api/add_room",
            json={"room_name": room_name}
        )
        if response.json().get("status") == "success":
            await update.message.reply_text(f'Комната "{room_name}" создана.')
        else:
            await update.message.reply_text("Ошибка при создании комнаты.")
    else:
        await update.message.reply_text("Используйте: /newroom <название комнаты>")

# Обработчик сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    room_name = "Общая комната"  # Замените на логику выбора комнаты
    message_text = update.message.text
    sender = update.message.from_user.first_name

    # Отправляем данные на API
    response = requests.post(
        f"{API_URL}/api/send_message",
        json={
            "room_name": room_name,
            "sender": sender,
            "message": message_text
        }
    )
    if response.json().get("status") == "success":
        await update.message.reply_text(f'Сообщение отправлено в комнату "{room_name}".')
    else:
        await update.message.reply_text("Ошибка при отправке сообщения.")

def main() -> None:
    # Вставьте сюда ваш токен
    application = Application.builder().token("7872778132:AAGJF2Ueejc4VdasF2QTECEehKdJa5_rTQg").build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newroom", new_room))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()