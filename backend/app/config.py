from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/revenue_agent"
    REDIS_URL: str = "redis://default:AZzPAAIncDJkZDM3MGYyNjZlOGQ0NjQ4OWZjZmE4NDc5Nzg5MGU4YXAyNDAxNDM@solid-donkey-40143.upstash.io:6379"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ANTHROPIC_API_KEY: str = ""
        # SendGrid (Email)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""

    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # class Config:
    #     env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

