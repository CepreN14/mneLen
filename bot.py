# bot.py
import os
import telegram
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID","0"))

# Define the /start command handler
async def start(update: Update, context: CallbackContext):
    """Sends a message with a button that opens the Web App."""
    keyboard = [
        [telegram.KeyboardButton(
            text="Open Web App",
            web_app=WebAppInfo(url="https://cepren14.github.io/mneLen/") # todo: Replace url
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Please press the button to start the web app:", reply_markup=reply_markup)

async def post_init(application: ApplicationBuilder):
    await application.bot.set_my_commands([
        ('start', 'Запустить бота'),
    ])

# Main function to set up the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Define command handlers
    start_handler = CommandHandler('start', start)

    # Add command handlers to the application
    application.add_handler(start_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
