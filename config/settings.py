from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bot.db"
    APTOS_GRAPHQL_URL: str = "https://api.mainnet.aptoslabs.com/v1/graphql"
    APTOS_NETWORK: str = "mainnet"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

