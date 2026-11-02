import os
import time
import logging
import telebot
from telebot import types
from flask import Flask, request, abort, jsonify

# =========================
# НАСТРОЙКИ
# =========================

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not all([TOKEN, ADMIN_ID, WEBHOOK_SECRET, BASE_URL]):
    raise RuntimeError("Не заданы переменные окружения!")

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
    logging.info("Получена команда /start от %s",
                 message.from_user.id)

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
        f"📨 Нажатий на кнопки: {MESSAGE_COUNT}\n"
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
# WEBHOOK И ДИАГНОСТИКА
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Blox Fruits Control is running!", 200


@app.route("/test", methods=["GET"])
def test():
    try:
        info = bot.get_webhook_info()

        return jsonify({
            "server": "running",
            "webhook_url": info.url,
            "pending_updates": info.pending_update_count,
            "last_error": info.last_error_message
        })
    except Exception as e:
        logging.exception("Ошибка проверки webhook")
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if received_secret != WEBHOOK_SECRET:
        logging.warning("Неверный секрет webhook")
        abort(403)

    data = request.get_json(silent=True)

    if not data:
        logging.warning("Получен пустой запрос")
        return "Empty update", 400

    try:
        update = telebot.types.Update.de_json(data)

        logging.info("Получено обновление Telegram")

        bot.process_new_updates([update])

        return "OK", 200

    except Exception:
        logging.exception("Ошибка обработки обновления")
        return "Internal error", 500


# =========================
# ЗАПУСК WEBHOOK
# =========================

webhook_url = BASE_URL.rstrip("/") + "/webhook"

try:
    result = bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET
    )

    logging.info("Webhook registration result: %s", result)
    logging.info("Webhook URL: %s", webhook_url)

except Exception:
    logging.exception("Не удалось зарегистрировать webhook")
    raise