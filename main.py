import asyncio

from settings import TOKEN, ADMIN_CHAT_ID

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# Определяем состояния диалога
DEPARTURE, DESTINATION, CARGO, DATETIME, CONTACT = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите точку отправления:\n"
                                    "Для отмены нажмите /cancel\n"
                                    "Для вывода справки нажмите /help")
    return DEPARTURE

async def get_departure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['departure'] = update.message.text
    await update.message.reply_text("Введите точку(и) назначения (если несколько, разделите запятой):")
    return DESTINATION

async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['destination'] = update.message.text
    await update.message.reply_text("Введите тип груза:")
    return CARGO

async def get_cargo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['cargo'] = update.message.text
    await update.message.reply_text("Введите желаемые дату и время (например, ДД.ММ.ГГГГ ЧЧ:ММ):")
    return DATETIME

async def get_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['datetime'] = update.message.text
    await update.message.reply_text("Введите ваш контактный номер телефона или email:")
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['contact'] = update.message.text
    # Получаем данные заявки
    departure = context.user_data.get('departure', 'Не указано')
    destination = context.user_data.get('destination', 'Не указано')
    cargo = context.user_data.get('cargo', 'Не указано')
    datetime_val = context.user_data.get('datetime', 'Не указано')
    contact = context.user_data.get('contact', 'Не указано')
    # Получаем chat_id пользователя
    user_chat_id = update.effective_chat.id

    # Формируем итоговое сообщение для администратора
    formatted_message = (
        f"📦 Новая заявка на перевозку:\n\n"
        f"🚚 Отправление: {departure}\n"
        f"📍 Назначение(я): {destination}\n"
        f"📦 Тип груза: {cargo}\n"
        f"⏳ Дата и время: {datetime_val}\n"
        f"☎️ Контакт: {contact}\n"
        f"🆔 Chat ID пользователя: {user_chat_id}"
    )

    # Отправляем сообщение администратору
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=formatted_message)
    await update.message.reply_text("✅ Ваша заявка принята. Ожидайте подтверждения!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Команда для администратора: отправка ответа пользователю.
# Использование: /reply <chat_id> <сообщение>
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Используйте: /reply <chat_id> <сообщение>")
        return
    try:
        target_chat_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Неверный chat_id.")
        return
    reply_text = " ".join(args[1:])
    await context.bot.send_message(chat_id=target_chat_id, text=f"Админ: {reply_text}")
    await update.message.reply_text("Сообщение отправлено.")

# Команда для вывода списка команд для обычного пользователя
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды для пользователя:\n"
        "/start - оформить новую заявку\n"
        "/cancel - отменить оформление заявки\n"
        "/help - вывести этот список команд\n"
    )
    await update.message.reply_text(help_text)

# Команда для вывода списка команд для администратора
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    admin_help_text = (
        "Доступные команды для администратора:\n"
        "/reply <chat_id> <сообщение> - ответить пользователю\n"
        "/admin_help - вывести этот список команд\n"
    )
    await update.message.reply_text(admin_help_text)

def main():
    # Замените токен на токен вашего бота
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DEPARTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_departure)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination)],
            CARGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cargo)],
            DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_datetime)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('reply', admin_reply))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('admin_help', admin_help))

    print("🚀 Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
