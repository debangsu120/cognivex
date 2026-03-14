from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # Groq
    groq_api_key: str

    # Deepgram (for audio transcription)
    deepgram_api_key: Optional[str] = None

    # Eleventh Labs (for text-to-speech)
    eleventh_labs_api_key: Optional[str] = None

    # App
    app_name: str = "AI Interview Platform"
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
