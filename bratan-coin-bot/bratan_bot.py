import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os
import json

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# URL твоего веб-приложения (ЗАМЕНИ НА СВОЙ!)
WEBAPP_URL = "https://amvera-maxim22221231-run-bratancoin-bot.amvera.io"  # ← Твой домен из Amvera

@bot.message_handler(commands=['start'])
def start_command(message):
    # Клавиатура с кнопкой открытия приложения
    keyboard = InlineKeyboardMarkup()
    web_app_button = InlineKeyboardButton(
        text="🚀 ЗАПУСТИТЬ БРАТАН КОИН 🚀",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    keyboard.add(web_app_button)
    
    bot.send_message(
        message.chat.id,
        f"""💎 БРАТАН КОИН 💎

👊 Здарова, {message.from_user.first_name}!

Нажимай на кнопку и ЗАПУСКАЙ ТАПАЛКУ!

🖱️ Жми по монетке
⚡️ Следи за энергией
🫘 Покупай бусты
🚗 Копи на Жигуль!

Погнали, братан! 👊""",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app(message):
    # Обработка данных из веб-приложения (если нужно)
    pass

print("🔥 Братан Коин с веб-интерфейсом запущен!")
bot.infinity_polling(skip_pending=True)