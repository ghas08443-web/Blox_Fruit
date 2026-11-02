
import os
import telebot
from telebot import types

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в GitHub Secrets")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID не найден в GitHub Secrets")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN)


# =========================
# ПРОВЕРКА ДОСТУПА
# =========================

def is_admin(message):
    return (
        message.from_user is not None
        and message.from_user.id == ADMIN_ID
    )


def deny_access(message):
    bot.reply_to(
        message,
        "⛔ У тебя нет доступа к панели."
    )


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "📊 Статус",
        "ℹ️ Помощь"
    )

    keyboard.row(
        "🔄 Проверка бота"
    )

    return keyboard


# =========================
# КОМАНДА START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    if not is_admin(message):
        deny_access(message)
        return

    bot.send_message(
        message.chat.id,
        "🍎 Blox Fruits Control\n\n"
        "🔐 Доступ подтверждён!\n"
        "Панель управления запущена.\n\n"
        "Выбери нужную кнопку:",
        reply_markup=main_menu()
    )


# =========================
# СТАТУС
# =========================

@bot.message_handler(commands=["status"])
def status(message):
    if not is_admin(message):
        deny_access(message)
        return

    bot.send_message(
        message.chat.id,
        "🟢 Telegram-бот работает.\n"
        "📡 Соединение активно."
    )


@bot.message_handler(
    func=lambda m: m.text == "📊 Статус"
)
def status_button(message):
    status(message)


# =========================
# ПОМОЩЬ
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):
    if not is_admin(message):
        deny_access(message)
        return

    bot.send_message(
        message.chat.id,
        "📋 Список команд:\n\n"
        "/start — открыть меню\n"
        "/status — проверить состояние\n"
        "/help — помощь"
    )


@bot.message_handler(
    func=lambda m: m.text == "ℹ️ Помощь"
)
def help_button(message):
    help_command(message)


# =========================
# ПРОВЕРКА БОТА
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🔄 Проверка бота"
)
def check_button(message):
    if not is_admin(message):
        deny_access(message)
        return

    bot.send_message(
        message.chat.id,
        "✅ Проверка пройдена!\n"
        "Бот принимает сообщения."
    )


# =========================
# ЗАПУСК
# =========================

print("Blox Fruits Control started!")

bot.infinity_polling()
