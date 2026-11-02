import os
import time
import telebot
from telebot import types
from flask import Flask, request, abort

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not all([TOKEN, ADMIN_ID, WEBHOOK_SECRET, BASE_URL]):
    raise RuntimeError("Не заданы все переменные окружения")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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
# КОМАНДЫ
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "🍎 Blox Fruits Control\n\n"
        "🔐 Доступ подтверждён!\n"
        "🟢 Панель активна.",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["status"])
def status(message):
    if not check_access(message):
        return

    uptime = int(time.time() - START_TIME)

    bot.send_message(
        message.chat.id,
        "📊 СОСТОЯНИЕ СИСТЕМЫ\n\n"
        "🟢 Telegram-бот: работает\n"
        f"⏱ Время работы: {uptime // 60} мин.\n"
        "📡 Соединение: активно\n"
        "🎮 Игровой клиент: не подключён"
    )


@bot.message_handler(commands=["stats"])
def stats(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "📈 СТАТИСТИКА\n\n"
        f"📨 Сообщений: {MESSAGE_COUNT}\n"
        f"⏱ Время работы: "
        f"{int(time.time() - START_TIME)} сек."
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "/start — меню\n"
        "/status — состояние\n"
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
            "✅ Проверка пройдена!"
        )

    elif message.text == "ℹ️ Помощь":
        help_command(message)


# =========================
# WEBHOOK
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Blox Fruits Control is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:
        abort(403)

    data = request.get_json(silent=True)

    if data:
        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])

    return "OK", 200


# =========================
# РЕГИСТРАЦИЯ WEBHOOK
# =========================

webhook_url = BASE_URL.rstrip("/") + "/webhook"

bot.set_webhook(
    url=webhook_url,
    secret_token=WEBHOOK_SECRET
)

print("Blox Fruits Control webhook started!")