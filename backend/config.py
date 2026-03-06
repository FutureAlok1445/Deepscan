import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path — check project root first, then backend/
_env_candidates = [
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
]
_env_file = next((p for p in _env_candidates if os.path.isfile(p)), ".env")


class Settings(BaseSettings):
    # ── App ──
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Database ──
    MONGO_URI: str = "mongodb://mongo:27017/deepscan"
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Auth ──
    JWT_SECRET: str = "change-this-to-random-64-char-secret"
    JWT_EXPIRE_HOURS: str = "24"

    # ── AI APIs ──
    ANTHROPIC_API_KEY: str = ""
    HF_API_TOKEN: str = ""
    HUGGINGFACE_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ── Telegram ──
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # ── External ──
    GOOGLE_TRANSLATE_KEY: str = ""
    NEWS_API_KEY: str = ""

    # ── Storage ──
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIR: str = os.path.join(os.environ.get("TEMP", "/tmp"), "deepscan_uploads")
    ALLOWED_EXTENSIONS: list = ["jpg", "png", "mp4", "wav", "mp3"]

    @property
    def cors_origins(self) -> list:
        """Parse ALLOWED_ORIGINS CSV into a list."""
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.DEBUG:
            for extra in [
                "http://localhost:3000", "http://localhost:5173",
                "http://127.0.0.1:3000", "http://127.0.0.1:5173",
            ]:
                if extra not in origins:
                    origins.append(extra)
        return origins

    model_config = SettingsConfigDict(
        env_file=_env_file,
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

# Inject into os.environ so modules that read os.getenv() directly can see them
if settings.HF_API_TOKEN:
    os.environ.setdefault("HF_API_TOKEN", settings.HF_API_TOKEN)
if settings.HUGGINGFACE_API_KEY:
    os.environ.setdefault("HUGGINGFACE_API_KEY", settings.HUGGINGFACE_API_KEY)
elif settings.HF_API_TOKEN:
    os.environ.setdefault("HUGGINGFACE_API_KEY", settings.HF_API_TOKEN)
if settings.GROQ_API_KEY:
    os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)