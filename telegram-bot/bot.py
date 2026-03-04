from telegram import Update
from telegram.ext import Application, CommandHandler
import os

async def start(u: Update, c): await u.message.reply_text("Send an image, video, or URL to analyze.")

if __name__ == '__main__':
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN", "mock-token")).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()\n