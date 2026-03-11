from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite:///./mydailyaudio.db"
    secret_key: str = "change-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    telegram_bot_token_default: Optional[str] = None
    telegram_chat_id_default: Optional[str] = None
    github_repo_name: str = "mydailyaudio"
    data_dir: str = "./data"
    output_base_url: str = "https://urright.github.io/mydailyaudio"

    class Config:
        env_file = ".env"

settings = Settings()