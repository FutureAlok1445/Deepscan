import os
from loguru import logger

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False
    logger.warning("python-telegram-bot not installed — bot features disabled")

from backend.services.bot.message_handler import handle_media, handle_text
from backend.services.bot.report_formatter import format_result


async def start(update: Update, context):
    """Handle /start command."""
    welcome = (
        "🔍 *Welcome to DeepScan Bot!*\n"
        "I analyze media for deepfakes using AI.\n\n"
        "📸 Send me an *image* to check\n"
        "🎬 Send a *video* for frame + rPPG analysis\n"
        "🎙️ Send *audio* for voice clone detection\n"
        "🔗 Send a *URL* to scan media from a webpage\n\n"
        "_Powered by AACS — AI Authenticity Confidence Score_\n"
        "_Team Bug Bytes • HackHive 2.0_"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_cmd(update: Update, context):
    """Handle /help command."""
    help_text = (
        "📋 *DeepScan Commands:*\n"
        "/start — Welcome message\n"
        "/help — Show this help\n"
        "/about — About AACS scoring\n\n"
        "Just send any image, video, or audio file and I'll analyze it!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_cmd(update: Update, context):
    """Handle /about command."""
    about = (
        "🧬 *AACS — AI Authenticity Confidence Score*\n\n"
        "Formula: `((0.30×MAS) + (0.25×PPS) + (0.20×IRS) + (0.15×AAS) + (0.10×CVS)) × CDCF`\n\n"
        "• *MAS* — Media Authenticity (EfficientNet-B4)\n"
        "• *PPS* — Physiological Plausibility (rPPG)\n"
        "• *IRS* — Information Reliability\n"
        "• *AAS* — Acoustic Anomaly Detection\n"
        "• *CVS* — Context Verification\n\n"
        "Score 0-30: ✅ Authentic\n"
        "Score 31-60: ⚠️ Uncertain\n"
        "Score 61-85: 🟠 Likely Fake\n"
        "Score 86-100: 🔴 Definitely Fake"
    )
    await update.message.reply_text(about, parse_mode="Markdown")


def build_app():
    """Build the Telegram bot application with all handlers."""
    if not HAS_TELEGRAM:
        logger.warning("python-telegram-bot not available — returning None")
        return None
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot will not function")

    app = Application.builder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))

    # Media handlers
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Telegram bot application built with all handlers")
    return app