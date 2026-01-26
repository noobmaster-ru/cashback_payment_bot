from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvSettings(BaseSettings):
    # Telegram
    BOT_TOKEN: str

    #Superbanking
    SUPERBANKING_API_KEY: str
    SUPERBANKING_CABINET_ID: str
    SUPERBANKING_PROJECT_ID: str
    SUPERBANKING_CLEARING_CENTER_ID: str

    # Redis
    REDIS_URL: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )