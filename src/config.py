import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(os.path.dirname(__file__))

load_dotenv()


@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_AUTO_FLUSH: bool = True
    DATABASE_EXPIRE_ON_COMMIT: bool = True

    YANDEX_GPT_API_KEY: str | None = os.getenv("YANDEX_GPT_API_KEY")
    YANDEX_ID_KEY: str | None = os.getenv("YANDEX_ID_KEY")
    YANDEX_FOLDER_ID: str | None = os.getenv("YANDEX_FOLDER_ID")

    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_PROXY_URL: str | None = os.getenv("TELEGRAM_PROXY_URL")

    GPT_PROMPT: str = os.getenv("GPT_PROMPT", "")

    MEMORY_USER_MESSAGE_LIMIT: int = int(os.getenv("MEMORY_USER_MESSAGE_LIMIT", "5"))
    MEMORY_LIMIT_WINDOW_MINUTES: int = int(os.getenv("MEMORY_LIMIT_WINDOW_MINUTES", "60"))
    MEMORY_RECENT_MESSAGES: int = int(os.getenv("MEMORY_RECENT_MESSAGES", "8"))
    MEMORY_SEARCH_RESULTS: int = int(os.getenv("MEMORY_SEARCH_RESULTS", "5"))
    MEMORY_SUMMARY_TRIGGER_MESSAGES: int = int(
        os.getenv("MEMORY_SUMMARY_TRIGGER_MESSAGES", "12")
    )
    MEMORY_SUMMARY_SOURCE_MESSAGES: int = int(
        os.getenv("MEMORY_SUMMARY_SOURCE_MESSAGES", "40")
    )


settings = Settings()
