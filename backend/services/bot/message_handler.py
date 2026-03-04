import os
import uuid
import asyncio
import tempfile
from loguru import logger

try:
    from telegram import Update
except ImportError:
    Update = None

from backend.services.detection.orchestrator import orchestrator
from backend.services.bot.report_formatter import format_result


async def handle_media(update: Update, context):
    """Handle incoming media files (photo, video, audio, documents)."""
    message = update.message
    await message.reply_text("⏳ Analyzing your media... This may take a moment.")

    try:
        # Determine file to download
        if message.photo:
            file_obj = await message.photo[-1].get_file()  # highest res
            ext = "jpg"
        elif message.video:
            file_obj = await message.video.get_file()
            ext = "mp4"
        elif message.audio:
            file_obj = await message.audio.get_file()
            ext = "mp3"
        elif message.voice:
            file_obj = await message.voice.get_file()
            ext = "ogg"
        elif message.document:
            file_obj = await message.document.get_file()
            ext = message.document.file_name.split(".")[-1] if message.document.file_name else "bin"
        else:
            await message.reply_text("❌ Unsupported media type. Send an image, video, or audio.")
            return

        # Download to temp location
        _tg_dir = os.path.join(tempfile.gettempdir(), "deepscan_telegram")
        os.makedirs(_tg_dir, exist_ok=True)
        file_path = os.path.join(_tg_dir, f"{uuid.uuid4().hex}.{ext}")
        await file_obj.download_to_drive(file_path)

        # Run analysis
        if not orchestrator.models_loaded:
            await orchestrator.load_models()

        mime_map = {"jpg": "image/jpeg", "png": "image/png", "mp4": "video/mp4",
                    "mp3": "audio/mpeg", "ogg": "audio/ogg", "wav": "audio/wav"}
        mime = mime_map.get(ext, "application/octet-stream")

        result = await orchestrator.process_media(file_path, mime)

        # Send formatted result
        response = format_result(result)
        await message.reply_text(response, parse_mode="Markdown")

        # Cleanup
        try:
            os.remove(file_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Telegram media handler error: {e}")
        await message.reply_text(f"❌ Analysis failed: {str(e)[:100]}")


async def handle_text(update: Update, context):
    """Handle text messages (URL detection or help)."""
    text = update.message.text.strip()

    if text.startswith("http://") or text.startswith("https://"):
        await update.message.reply_text("🔗 URL analysis coming soon! For now, download the media and send it directly.")
    else:
        await update.message.reply_text(
            "Send me an image, video, or audio file to analyze for deepfakes!\n"
            "Use /help for more info."
        )