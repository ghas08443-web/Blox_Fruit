import os
import time
import logging
import telebot
from telebot import types
from flask import Flask, request, abort, jsonify

# =====================================
# ЛОГИ И НАСТРОЙКИ
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not all([TOKEN, ADMIN_ID, WEBHOOK_SECRET, BASE_URL]):
    raise RuntimeError("Не заданы необходимые переменные окружения")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

START_TIME = time.time()
MESSAGE_COUNT = 0

FARM_RUNNING = False
FARM_MODE = "Обычный"
FARM_STARTED_AT = None

FARM_MODES = ["Обычный", "Быстрый", "Безопасный"]


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
        bot.reply_to(message, "⛔ Доступ запрещён.")
        return False
    return True


# =====================================
# КЛАВИАТУРЫ
# =====================================

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.row("🎮 Фарм", "📊 Статус")
    keyboard.row("📈 Статистика", "🔄 Проверка")
    keyboard.row("ℹ️ Помощь")

    return keyboard


def farm_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.row("▶️ Запустить", "⏹ Остановить")
    keyboard.row("🎯 Выбрать режим", "📊 Статус фарма")
    keyboard.row("⬅️ Главное меню")

    return keyboard


def mode_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for mode in FARM_MODES:
        keyboard.row(mode)

    keyboard.row("⬅️ Назад")

    return keyboard


# =====================================
# СОСТОЯНИЕ ФАРМА
# =====================================

def farm_status_text():
    global FARM_RUNNING, FARM_STARTED_AT

    if FARM_RUNNING:
        elapsed = int(time.time() - FARM_STARTED_AT)
        state = "🟢 Включён"
        duration = f"{elapsed // 60} мин. {elapsed % 60} сек."
    else:
        state = "🔴 Остановлен"
        duration = "—"

    return (
        "🎮 СОСТОЯНИЕ ФАРМА\n\n"
        f"Состояние: {state}\n"
        f"Режим: {FARM_MODE}\n"
        f"Время работы: {duration}\n\n"
        "ℹ️ Это панель состояния, игровой клиент не подключён."
    )


# =====================================
# КОМАНДЫ
# =====================================

@bot.message_handler(commands=["start"])
def start(message):
    global MESSAGE_COUNT

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
        "📡 Webhook: активен\n"
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
        f"⏱ Работа бота: {int(time.time() - START_TIME)} сек."
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "/start — меню\n"
        "/status — состояние системы\n"
        "/stats — статистика\n"
        "/help — помощь"
    )


# =====================================
# ОБРАБОТКА КНОПОК
# =====================================

@bot.message_handler(func=lambda m: m.text == "🎮 Фарм")
def open_farm(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "🎮 Панель режима фарма",
        reply_markup=farm_menu()
    )


@bot.message_handler(func=lambda m: m.text == "▶️ Запустить")
def start_farm(message):
    global FARM_RUNNING, FARM_STARTED_AT, MESSAGE_COUNT

    if not check_access(message):
        return

    if FARM_RUNNING:
        bot.send_message(message.chat.id, "⚠️ Режим уже включён.")
        return

    FARM_RUNNING = True
    FARM_STARTED_AT = time.time()
    MESSAGE_COUNT += 1

    bot.send_message(
        message.chat.id,
        "🟢 Режим включён.\n"
        f"Выбранный режим: {FARM_MODE}\n\n"
        "Это только переключатель состояния панели.",
        reply_markup=farm_menu()
    )


@bot.message_handler(func=lambda m: m.text == "⏹ Остановить")
def stop_farm(message):
    global FARM_RUNNING, FARM_STARTED_AT, MESSAGE_COUNT

    if not check_access(message):
        return

    FARM_RUNNING = False
    FARM_STARTED_AT = None
    MESSAGE_COUNT += 1

    bot.send_message(
        message.chat.id,
        "🔴 Режим остановлен.",
        reply_markup=farm_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🎯 Выбрать режим")
def choose_mode(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "Выбери режим:",
        reply_markup=mode_menu()
    )


@bot.message_handler(func=lambda m: m.text in FARM_MODES)
def set_mode(message):
    global FARM_MODE

    if not check_access(message):
        return

    if FARM_RUNNING:
        bot.send_message(
            message.chat.id,
            "Сначала останови текущий режим."
        )
        return

    FARM_MODE = message.text

    bot.send_message(
        message.chat.id,
        f"✅ Выбран режим: {FARM_MODE}",
        reply_markup=farm_menu()
    )


@bot.message_handler(func=lambda m: m.text == "📊 Статус фарма")
def show_farm_status(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        farm_status_text(),
        reply_markup=farm_menu()
    )


@bot.message_handler(func=lambda m: m.text == "⬅️ Главное меню")
def back_main(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "Главное меню:",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back_farm(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "Панель фарма:",
        reply_markup=farm_menu()
    )


@bot.message_handler(
    func=lambda m: m.text in [
        "📊 Статус",
        "📈 Статистика",
        "🔄 Проверка",
        "ℹ️ Помощь"
    ]
)
def main_buttons(message):
    if not check_access(message):
        return

    if message.text == "📊 Статус":
        status(message)
    elif message.text == "📈 Статистика":
        stats(message)
    elif message.text == "🔄 Проверка":
        bot.send_message(message.chat.id, "✅ Проверка пройдена!")
    elif message.text == "ℹ️ Помощь":
        help_command(message)


# =====================================
# НЕИЗВЕСТНЫЕ СООБЩЕНИЯ
# =====================================

@bot.message_handler(func=lambda m: True)
def unknown_message(message):
    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        "Не понял команду. Используй /help."
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
        return jsonify({"error": "Не удалось проверить webhook"}), 500


# =====================================
# WEBHOOK
# =====================================

@app.route("/webhook", methods=["POST"])
def webhook():
    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if received_secret != WEBHOOK_SECRET:
        abort(403)

    data = request.get_json(silent=True)

    if not data:
        return "Empty update", 400

    try:
        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])
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