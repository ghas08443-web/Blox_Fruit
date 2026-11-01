
import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = telebot.TeleBot(TOKEN)


def main_menu():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row("📊 Статус", "ℹ️ Помощь")
    keyboard.row("🔄 Проверка бота")

    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🍎 Blox Fruits Control\n\n"
        "Панель управления запущена!\n"
        "Выбери нужную кнопку:",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["status"])
def status(message):
    bot.send_message(
        message.chat.id,
        "🟢 Telegram-бот отвечает.\n"
        "📡 Соединение активно."
    )


@bot.message_handler(func=lambda m: m.text == "📊 Статус")
def status_button(message):
    status(message)


@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_button(message):
    bot.send_message(
        message.chat.id,
        "📋 Команды:\n\n"
        "/start — открыть меню\n"
        "/status — проверить бота"
    )


@bot.message_handler(func=lambda m: m.text == "🔄 Проверка бота")
def check_button(message):
    bot.send_message(
        message.chat.id,
        "✅ Проверка пройдена!\n"
        "Бот принимает сообщения."
    )


print("Telegram bot started!")
bot.infinity_polling()
