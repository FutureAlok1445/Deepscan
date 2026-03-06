from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    MONGO_URI: str = "mongodb://mongo:27017/deepscan"
    POSTGRES_URI: str = "postgresql+asyncpg://user:pass@localhost/deepscan"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-this-to-random-64-char-secret"
    JWT_EXPIRE_HOURS: int = 24
    ANTHROPIC_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    GOOGLE_TRANSLATE_KEY: str = ""
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    NEWS_API_KEY: str = ""
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: list = ["jpg", "png", "mp4", "wav", "mp3"]
    HF_API_TOKEN: str = ""

    class Config:
        env_file = ".env"

settings = Settings()