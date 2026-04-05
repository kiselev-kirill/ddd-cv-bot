import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any

from src.config import BASE_DIR

VERBOSE_FORMATTER = logging.Formatter(
    "[%(asctime)s] [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BotLogger:

    @staticmethod
    def setup_logger():
        log_file = BASE_DIR / "bot.log"
        handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=5_485_760,
            backupCount=3,
            encoding="utf-8"
        )
        handler.setFormatter(VERBOSE_FORMATTER)

        logger = logging.getLogger("bot")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            logger.addHandler(handler)
        logger.propagate = False

        return logger


bot_logger = BotLogger.setup_logger()


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    bot_logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
