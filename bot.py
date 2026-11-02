import os
import time
import telebot
from telebot import types

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID не найден")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN)

START_TIME = time.time()
MESSAGE_COUNT = 0


# =========================
# ДОСТУП
# =========================

def is_admin(message):
    return (
        message.from_user is not None
        and message.from_user.id == ADMIN_ID
    )


def check_access(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔ Доступ запрещён.")
        return False
    return True


# =========================
# МЕНЮ
# =========================

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row("📊 Статус", "📈 Статистика")
    keyboard.row("🔄 Проверка", "ℹ️ Помощь")

    return keyboard


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "🍎 Blox Fruits Control\n\n"
        "🔐 Доступ подтверждён!\n"
        "🟢 Telegram-панель активна.\n\n"
        "Выбери действие:",
        reply_markup=main_menu()
    )


# =========================
# СТАТУС
# =========================

@bot.message_handler(commands=["status"])
def status(message):
    if not check_access(message):
        return

    uptime = int(time.time() - START_TIME)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60

    bot.send_message(
        message.chat.id,
        "📊 СОСТОЯНИЕ СИСТЕМЫ\n\n"
        "🟢 Telegram-бот: работает\n"
        "⏱ Время работы: "
        f"{hours} ч. {minutes} мин. {seconds} сек.\n"
        "📡 Соединение с Telegram: активно\n"
        "🎮 Игровой клиент: не подключён"
    )


# =========================
# СТАТИСТИКА
# =========================

@bot.message_handler(commands=["stats"])
def stats(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "📈 СТАТИСТИКА\n\n"
        f"📨 Получено сообщений: {MESSAGE_COUNT}\n"
        f"⏱ Время работы: {int(time.time() - START_TIME)} секунд\n"
        "🟢 Состояние: активно"
    )


# =========================
# ПОМОЩЬ
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "ℹ️ КОМАНДЫ\n\n"
        "/start — открыть меню\n"
        "/status — состояние системы\n"
        "/stats — статистика\n"
        "/help — помощь"
    )


# =========================
# КНОПКИ
# =========================

@bot.message_handler(
    func=lambda m: m.text in [
        "📊 Статус",
        "📈 Статистика",
        "🔄 Проверка",
        "ℹ️ Помощь"
    ]
)
def buttons(message):
    global MESSAGE_COUNT

    if not check_access(message):
        return

    MESSAGE_COUNT += 1

    if message.text == "📊 Статус":
        status(message)

    elif message.text == "📈 Статистика":
        stats(message)

    elif message.text == "🔄 Проверка":
        bot.send_message(
            message.chat.id,
            "✅ Проверка пройдена!\n"
            "Telegram-бот отвечает."
        )

    elif message.text == "ℹ️ Помощь":
        help_command(message)


# =========================
# ЗАПУСК
# =========================

print("Blox Fruits Control started!")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)