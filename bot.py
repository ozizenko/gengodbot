import os
from telegram import Update, ReplyKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, PreCheckoutQueryHandler
from openai import OpenAI
from database import get_user, add_request, set_premium, extend_premium, save_message, get_memory

TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

keyboard = ReplyKeyboardMarkup([
    ["💎 Premium", "👤 Профиль"]
], resize_keyboard=True)

def ask_ai(user_id, text):
    history = get_memory(user_id)

    messages = [{"role": "system", "content": "Ты умный AI ассистент GenGodbot"}]

    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": text})

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return r.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("Привет! Я GenGodbot 🤖", reply_markup=keyboard)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    user = get_user(user_id)

    if text == "💎 Premium":
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title="TEST 100 STARS",
            description="Тестовая подписка",
            payload="premium",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Premium", 100)]
        )
        return

    if text == "👤 Профиль":
        await update.message.reply_text(f"ID: {user_id}\nЗапросов: {user[1]}")
        return

    save_message(user_id, "user", text)

    answer = ask_ai(user_id, text)

    save_message(user_id, "assistant", answer)

    add_request(user_id)

    await update.message.reply_text(answer)

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    extend_premium(user_id, 30)

    await update.message.reply_text("💎 Premium активирован на 30 дней!")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
# redeploy
