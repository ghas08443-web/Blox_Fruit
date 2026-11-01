import os
import telebot

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🍎 Blox Fruits Control\n\n"
        "Бот работает!\n"
        "Команда /status — проверить состояние."
    )

@bot.message_handler(commands=["status"])
def status(message):
    bot.reply_to(message, "🟢 Telegram-бот запущен.")

bot.infinity_polling()
