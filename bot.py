import os
import time
import logging
import telebot
from telebot import types
from flask import Flask, request, abort, jsonify

# =====================================
# ЛОГИ
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =====================================
# НАСТРОЙКИ
# =====================================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID не задан")

if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET не задан")

if not BASE_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL не задан")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

START_TIME = time.time()
MESSAGE_COUNT = 0


# =====================================
# ДОСТУП
# =====================================

def is_admin(message):
    return (
        message.from_user is not None
        and message.from_user.id == ADMIN_ID
    )


def check_access(message):
    if not is_admin(message):
        logging.warning(
            "ACCESS DENIED: user_id=%s, admin_id=%s",
            message.from_user.id if message.from_user else None,
            ADMIN_ID
        )

        bot.reply_to(message, "⛔ Доступ запрещён.")
        return False

    return True


# =====================================
# МЕНЮ
# =====================================

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row("📊 Статус", "📈 Статистика")
    keyboard.row("🔄 Проверка", "ℹ️ Помощь")

    return keyboard


# =====================================
# КОМАНДЫ
# =====================================

@bot.message_handler(commands=["start"])
def start(message):
    global MESSAGE_COUNT

    logging.info(
        "START HANDLER: user_id=%s, text=%r",
        message.from_user.id,
        message.text
    )

    try:
        if not check_access(message):
            return

        bot.send_message(
            message.chat.id,
            "🍎 Blox Fruits Control\n\n"
            "🔐 Доступ подтверждён!\n"
            "🟢 Панель активна.",
            reply_markup=main_menu()
        )

        MESSAGE_COUNT += 1
        logging.info("START RESPONSE SENT")

    except Exception:
        logging.exception("START HANDLER ERROR")


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
        f"📨 Обработано сообщений: {MESSAGE_COUNT}\n"
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


# =====================================
# КНОПКИ
# =====================================

@bot.message_handler(
    func=lambda message: message.text in [
        "📊 Статус",
        "📈 Статистика",
        "🔄 Проверка",
        "ℹ️ Помощь"
    ]
)
def buttons(message):
    global MESSAGE_COUNT

    logging.info(
        "BUTTON HANDLER: user_id=%s text=%r",
        message.from_user.id,
        message.text
    )

    if not check_access(message):
        return

    try:
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

        MESSAGE_COUNT += 1

    except Exception:
        logging.exception("BUTTON HANDLER ERROR")


# =====================================
# НЕИЗВЕСТНЫЕ СООБЩЕНИЯ
# =====================================

@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    logging.info(
        "UNKNOWN MESSAGE: user_id=%s text=%r",
        message.from_user.id if message.from_user else None,
        message.text
    )

    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "Не понял команду. Используй меню или /help."
    )


# =====================================
# FLASK
# =====================================

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

    except Exception:
        logging.exception("TEST ERROR")
        return jsonify({
            "error": "Не удалось проверить webhook"
        }), 500


# =====================================
# WEBHOOK
# =====================================

@app.route("/webhook", methods=["POST"])
def webhook():

    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if received_secret != WEBHOOK_SECRET:
        logging.warning("WEBHOOK: неправильный секрет")
        abort(403)

    data = request.get_json(silent=True)

    if not data:
        logging.warning("WEBHOOK: пустое обновление")
        return "Empty update", 400

    try:
        update = telebot.types.Update.de_json(data)

        # ПОДРОБНАЯ ДИАГНОСТИКА
        logging.info("UPDATE DATA: %s", data)

        if update.message:
            logging.info(
                "MESSAGE RECEIVED: text=%r user_id=%s",
                update.message.text,
                update.message.from_user.id
                if update.message.from_user else None
            )

        elif update.edited_message:
            logging.info("UPDATE TYPE: edited_message")

        elif update.callback_query:
            logging.info("UPDATE TYPE: callback_query")

        else:
            logging.info("UPDATE TYPE: other")

        # ОБРАБОТКА ОБНОВЛЕНИЯ
        bot.process_new_updates([update])

        logging.info("UPDATE PROCESSING FINISHED")

        return "OK", 200

    except Exception:
        logging.exception("WEBHOOK PROCESSING ERROR")
        return "Internal error", 500


# =====================================
# РЕГИСТРАЦИЯ WEBHOOK
# =====================================

webhook_url = BASE_URL.rstrip("/") + "/webhook"

try:
    bot.remove_webhook()
    time.sleep(1)

    result = bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET
    )

    logging.info("WEBHOOK REGISTERED: %s", result)
    logging.info("WEBHOOK URL: %s", webhook_url)

except Exception:
    logging.exception("WEBHOOK REGISTRATION ERROR")
    raise