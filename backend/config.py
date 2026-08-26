from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./nexus_smb.db"
    SECRET_KEY: str = "change-this-secret-key-before-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    GEMINI_API_KEY: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
