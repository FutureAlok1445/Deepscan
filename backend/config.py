import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path — check project root first, then backend/
_env_candidates = [
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
]
_env_file = next((p for p in _env_candidates if os.path.isfile(p)), ".env")

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    MONGO_URI: str = "mongodb://mongo:27017/deepscan"
    POSTGRES_URI: str = "postgresql+asyncpg://user:pass@localhost/deepscan"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-this-to-random-64-char-secret"
    JWT_EXPIRE_HOURS: str = "24"
    ANTHROPIC_API_KEY: str = ""
    HF_API_TOKEN: str = "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"
    HUGGINGFACE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    GOOGLE_TRANSLATE_KEY: str = ""
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    MAX_FILE_SIZE_MB: str = "500"
    ALLOWED_EXTENSIONS: list = ["jpg", "png", "mp4", "wav", "mp3"]
    NEWS_API_KEY: str = ""
    SAPLING_API_KEY: str = "WiThm47XLf39l57MORZ1wgAv4ntE0_8qy7c2rWLC7g0nFeCXydkZTsEjtNnQX2gSmKjFhBfYRtolA6_M2-T2og=="
    TELEGRAM_WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=_env_file,
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()

# Also inject into os.environ so modules that read os.getenv() directly can see them
if settings.HF_API_TOKEN:
    os.environ.setdefault("HF_API_TOKEN", settings.HF_API_TOKEN)
if settings.HUGGINGFACE_API_KEY:
    os.environ.setdefault("HUGGINGFACE_API_KEY", settings.HUGGINGFACE_API_KEY)
elif settings.HF_API_TOKEN:
    os.environ.setdefault("HUGGINGFACE_API_KEY", settings.HF_API_TOKEN)
if settings.GROQ_API_KEY:
    os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)