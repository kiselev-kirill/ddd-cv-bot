import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
BASE_DIR = Path(os.path.dirname(__file__))

load_dotenv()

@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = ""
    DATABASE_AUTO_FLUSH: bool = True
    DATABASE_EXPIRE_ON_COMMIT: bool = True

    YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
    YANDEX_ID_KEY = os.getenv("YANDEX_ID_KEY")
    YANDEX_FOLDER_ID=os.getenv("YANDEX_FOLDER_ID")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    GPT_PROMPT = os.getenv("GPT_PROMPT")


settings = Settings()

print(3773, settings.TELEGRAM_BOT_TOKEN)