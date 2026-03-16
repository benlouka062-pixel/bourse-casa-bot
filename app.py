import os
import logging
from flask import Flask
from telegram.ext import Application, CommandHandler
import threading
import time

BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def start(update, context):
    await update.message.reply_text("✅ Bot actif sur Railway !")

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

@app.route('/')
def index():
    return "✅ Bot Taoussi OK"

def run_bot():
    while True:
        try:
            application.run_polling()
        except Exception as e:
            logger.error(f"Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
