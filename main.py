import logging
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# === Настройки ===
TOKEN = "7572990762:AAEv_Zjk1NK8FMJtwz2s42usKSn42y8zXA0"

# === Логирование ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === Состояния ===
ASK_WAKE, ASK_SLEEP = range(2)

# === Словарь данных пользователей ===
user_data = {}

# === Старт ===
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "wake": None,
        "sleep": None,
        "last_done": None,
    }
    update.message.reply_text("Привет! 🏋️‍♀️ Во сколько ты обычно просыпаешься? (Например, 07:30)")
    return ASK_WAKE

# === Получаем время пробуждения ===
def ask_wake(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        wake_time = datetime.strptime(update.message.text, "%H:%M").time()
        user_data[user_id]["wake"] = wake_time
        update.message.reply_text("А во сколько ложишься спать? (Например, 22:30)")
        return ASK_SLEEP
    except:
        update.message.reply_text("Пожалуйста, введи время в формате ЧЧ:ММ, например 08:00.")
        return ASK_WAKE

# === Получаем время сна ===
def ask_sleep(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        sleep_time = datetime.strptime(update.message.text, "%H:%M").time()
        user_data[user_id]["sleep"] = sleep_time
        update.message.reply_text("Готово! Я буду напоминать тебе о тренировках каждый час 💪")
        return ConversationHandler.END
    except:
        update.message.reply_text("Формат должен быть ЧЧ:ММ. Попробуй ещё раз.")
        return ASK_SLEEP

# === Кнопка "Я потренировался" ===
def send_workout_button(context: CallbackContext):
    for user_id, data in user_data.items():
        now = datetime.now()
        today = now.date()

        # Проверка: время внутри интервала бодрствования
        wake = data.get("wake")
        sleep = data.get("sleep")
        last_done = data.get("last_done")

        if not wake or not sleep:
            continue

        current_time = now.time()

        if wake <= current_time <= sleep:
            if last_done != today:
                # Выбор текста в зависимости от времени
                hour = now.hour
                if 5 <= hour < 12:
                    text = "☀ Доброе утро, солнышко! Пора размять свои косточки!"
                elif 12 <= hour < 18:
                    text = "🏃‍♀️ Уже день, а ты всё ещё не двигался. Вперёд за движением!"
                else:
                    text = "🌙 Уже вечер... пора размяться перед сном."

                keyboard = [[InlineKeyboardButton("✅ Я потренировался!", callback_data="workout_done")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)

# === Обработка кнопки ===
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    today = datetime.now().date()

    if user_data[user_id]["last_done"] == today:
        query.edit_message_text("Ты уже отметил тренировку сегодня ✅")
    else:
        user_data[user_id]["last_done"] = today
        query.edit_message_text("🔥 Молодец! Тренировка записана!")

# === Обработчик ошибок ===
def error(update, context):
    print(f"Ошибка: {context.error}")

# === Основная функция ===
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обработка команд
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_WAKE: [MessageHandler(Filters.text & ~Filters.command, ask_wake)],
            ASK_SLEEP: [MessageHandler(Filters.text & ~Filters.command, ask_sleep)],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_error_handler(error)

    # Планировщик уведомлений
    job_queue = updater.job_queue
    job_queue.run_repeating(send_workout_button, interval=3600, first=10)  # каждый час

    # Запуск
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

