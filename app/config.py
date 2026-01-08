import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "WhatsApp Ingestion Service"
    # Default to a file in /data for Docker persistence
    DATABASE_URL: str = "/data/app.db"
    WEBHOOK_SECRET: str
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

# Defer instantiation to runtime
def get_settings():
    return Settings()
