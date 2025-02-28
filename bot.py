# bot.py
import os
import telegram
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import pytz
from datetime import time, datetime
import logging
import requests  # Убедитесь, что requests установлен

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Состояния для диалога
SET_NAME, SET_TIMEZONE, SET_WORKING_HOURS, SET_WORKING_HOURS_END, SET_ROLE = range(5)

# Вспомогательные функции
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- Обработчики ---
async def start(update: Update, context: CallbackContext):
    """Обрабатывает команду /start."""
    user = await authenticate_user(update, context)

    if not user or not user.get('display_name'): # Если пользователь не аутентифицирован или у него нет имени
      await update.message.reply_text("Привет! Я чат-бот для работы с Telegram Web App. Пожалуйста, введите ваше имя, которое будет отображаться в чатах:")
      return SET_NAME

    if not user.get('role'):
        keyboard = [
            ["Разработчик", "Заказчик"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Пожалуйста, выберите свою роль:", reply_markup=reply_markup)
        return SET_ROLE

    role = user.get('role')
    welcome_message = f"Привет, {user.get('display_name')} ({role})! " \
                      f"Нажмите кнопку, чтобы открыть веб-приложение:"

    if not WEB_APP_URL:
        await update.message.reply_text("Веб-приложение не настроено. Проверьте .env файл.")
        return ConversationHandler.END  # Завершить диалог, если нет URL веб-приложения

    keyboard = [
        [KeyboardButton(
            text="Открыть Web App",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END

async def set_name(update: Update, context: CallbackContext):
    """Обрабатывает установку имени пользователя."""
    user_name = update.message.text
    context.user_data['user_name'] = user_name
    await update.message.reply_text(f"Отлично, теперь ваше имя: {user_name}. Теперь, пожалуйста, укажите свой часовой пояс (например, Europe/Moscow):")
    return SET_TIMEZONE

async def set_timezone(update: Update, context: CallbackContext):
    """Обрабатывает установку часового пояса пользователя."""
    timezone_str = update.message.text
    try:
        pytz.timezone(timezone_str) # Проверка строки часового пояса
        context.user_data['timezone'] = timezone_str
        await update.message.reply_text(f"Отлично, ваш часовой пояс: {timezone_str}. Теперь укажите ваше рабочее время. Сначала время начала рабочего дня в формате ЧЧ:ММ (например, 09:00)")
        return SET_WORKING_HOURS
    except pytz.exceptions.UnknownTimeZoneError:
        await update.message.reply_text("Неверный часовой пояс. Пожалуйста, введите часовой пояс, например, Europe/Moscow:")
        return SET_TIMEZONE # Повторить ввод часового пояса

async def set_working_hours(update: Update, context: CallbackContext):
    """Обрабатывает установку рабочего времени пользователя."""
    try:
        start_time_str = update.message.text
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        context.user_data['working_hours_start'] = start_time

        await update.message.reply_text("Теперь время окончания рабочего дня в формате ЧЧ:ММ (например, 18:00)")
        return SET_WORKING_HOURS_END  # Переход к следующему состоянию для получения времени окончания
    except ValueError:
        await update.message.reply_text("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 09:00)")
        return SET_WORKING_HOURS # Повторить ввод времени начала

async def set_working_hours_end(update: Update, context: CallbackContext):
    """Обрабатывает установку времени окончания рабочего дня пользователя."""
    try:
        end_time_str = update.message.text
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        context.user_data['working_hours_end'] = end_time

        # --- Сохранить информацию о пользователе в Flask app ---
        user_id = update.message.from_user.id
        user_name = context.user_data.get('user_name')
        timezone = context.user_data.get('timezone')
        start_time = context.user_data.get('working_hours_start')
        end_time = end_time

        # Подготовить данные для вызова API
        user_data = {
            "telegram_id": user_id,
            "display_name": user_name,
            "timezone": timezone,
            "working_hours_start": start_time.isoformat(),
            "working_hours_end": end_time.isoformat()
        }

        # Вызов API Flask backend
        try:
            #  API Endpoint URL
            api_url = 'http://127.0.0.1:3000/api/users'
            response = requests.post(api_url, json=user_data)
            response.raise_for_status()  # Вызвать исключение для плохих кодов статуса
            await update.message.reply_text(f"Ваши данные успешно сохранены.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при сохранении пользователя: {e}")
            await update.message.reply_text(f"Произошла ошибка при сохранении данных. Обратитесь к администратору.")

        return ConversationHandler.END  # Завершить диалог
    except ValueError:
        await update.message.reply_text("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 18:00)")
        return SET_WORKING_HOURS_END # Повторить ввод времени окончания

async def help_command(update: Update, context: CallbackContext):
    """Обрабатывает команду /help."""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Запуск бота и регистрация\n"
        "/help - Помощь\n"
        "/create_room [Название комнаты] - Создать комнату (только для администраторов)\n"
        "/add_user_to_room - Добавить пользователя в комнату (только для администраторов)\n"
        "/list_rooms - Список комнат, в которых вы состоите"
    )

async def create_room(update: Update, context: CallbackContext):
    """Обрабатывает команду /create_room."""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("У вас нет прав для создания комнат.")
        return

    room_name = " ".join(context.args) # получить имя комнаты
    if not room_name:
        await update.message.reply_text("Пожалуйста, укажите название комнаты после команды /create_room.")
        return

    #  API Endpoint URL
    api_url = f'http://127.0.0.1:3000/api/rooms'
    try:
        headers = {'Content-Type': 'application/json'}
        data = {'creator_id': update.message.from_user.id, 'room_name': room_name}
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()

        await update.message.reply_text(f"Комната '{room_name}' успешно создана!")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при создании комнаты: {e}")
        await update.message.reply_text(f"Произошла ошибка при создании комнаты: {e}")

async def add_user_to_room(update: Update, context: CallbackContext):
    """Обрабатывает команду /add_user_to_room."""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("У вас нет прав для добавления пользователей в комнаты.")
        return

    # Здесь мы предполагаем, что получаем имя пользователя и название комнаты в качестве параметров
    # Например: /add_user_to_room имя_пользователя название_комнаты
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Пожалуйста, укажите имя пользователя и название комнаты после команды /add_user_to_room.")
        return

    user_name, room_name = args

    #  API Endpoint URL
    api_url = f'http://127.0.0.1:3000/api/users'
    try:
        headers = {'Content-Type': 'application/json'}
        data = {'user_name': user_name, 'room_name': room_name}
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()

        await update.message.reply_text(f"Пользователь '{user_name}' успешно добавлен в комнату '{room_name}'!")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при добавлении пользователя в комнату: {e}")
        await update.message.reply_text(f"Произошла ошибка при добавлении пользователя: {e}")

async def list_rooms(update: Update, context: CallbackContext):
    """Обрабатывает команду /list_rooms."""
    try:
        #  API Endpoint URL
        api_url = f'http://127.0.0.1:3000/api/rooms'
        response = requests.get(api_url)
        response.raise_for_status()

        rooms = response.json().get('rooms', [])
        if rooms:
            room_list = "\n".join([f"- {room['name']}" for room in rooms])
            await update.message.reply_text(f"Вы состоите в следующих комнатах:\n{room_list}")
        else:
            await update.message.reply_text("Вы не состоите ни в одной комнате.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении списка комнат: {e}")
        await update.message.reply_text(f"Произошла ошибка при получении списка комнат: {e}")

async def authenticate_user(update: Update, context: CallbackContext):
    """Authenticates user, creates a new user if not exists."""
    telegram_id = update.message.from_user.id
    #  API Endpoint URL
    api_url = f'http://127.0.0.1:3000/api/users/{telegram_id}' # Предполагаем, что есть GET endpoint для получения информации о пользователе
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        user_data = response.json() # Ожидаем данные пользователя в JSON формате
        return user_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при аутентификации пользователя: {e}")
        return None

async def set_role(update: Update, context: CallbackContext):
    """Sets the user's role."""
    role = update.message.text.lower()
    if role not in ["разработчик", "заказчик"]:
        await update.message.reply_text("Пожалуйста, выберите роль из предложенных вариантов.")
        return SET_ROLE

    context.user_data['role'] = role

    # Send data to API to save the user's role
    user_id = update.message.from_user.id
    user_name = context.user_data.get('user_name')
    timezone = context.user_data.get('timezone')
    start_time = context.user_data.get('working_hours_start')
    end_time = context.user_data.get('working_hours_end')

    user_data = {
        "telegram_id": user_id,
        "display_name": user_name,
        "timezone": timezone,
        "working_hours_start": start_time,
        "working_hours_end": end_time,
        "role": role # Send the role
    }

    try:
        api_url = 'http://127.0.0.1:3000/api/users'
        response = requests.post(api_url, json=user_data)
        response.raise_for_status()

        await update.message.reply_text(f"Роль успешно установлена как {role}.")
        await start(update, context) # Go to the next step (start again)
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при сохранении роли пользователя: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении роли. Пожалуйста, попробуйте позже.")

    return ConversationHandler.END

async def post_init(application: ApplicationBuilder):
    await application.bot.set_my_commands([
        ('start', 'Запустить веб-приложение'),
        ('help', 'Помощь'),
        ('create_room', 'Создать комнату (только для администраторов)'),
        ('add_user_to_room', 'Добавить пользователя в комнату (только для администраторов)'),
        ('list_rooms', 'Список комнат, в которых вы состоите'),
    ])

# --- Main ---
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            SET_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_timezone)],
            SET_WORKING_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_working_hours)],
            SET_WORKING_HOURS_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_working_hours_end)],
            SET_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_role)],
        },
        fallbacks=[CommandHandler('cancel', start)]  # Использовать start для отмены
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_room", create_room))
    application.add_handler(CommandHandler("add_user_to_room", add_user_to_room))
    application.add_handler(CommandHandler("list_rooms", list_rooms))

    application.run_polling()

if __name__ == '__main__':
    main()
