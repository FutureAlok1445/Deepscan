from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram bot webhook updates."""
    try:
        body = await request.json()
        logger.info(f"Telegram webhook: {body.get('update_id', 'unknown')}")

        # Extract message info
        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if text == "/start":
            return {"method": "sendMessage", "chat_id": chat_id,
                    "text": "Welcome to DeepScan Bot! Send me an image, video, or audio to analyze for deepfakes."}

        # Check for media
        has_media = any(message.get(k) for k in ["photo", "video", "audio", "voice", "document"])
        if has_media:
            return {"method": "sendMessage", "chat_id": chat_id,
                    "text": "Media received! Analysis is being processed. You'll receive the result shortly."}

        return {"method": "sendMessage", "chat_id": chat_id,
                "text": "Send me an image, video, or audio file to check for deepfakes."}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}