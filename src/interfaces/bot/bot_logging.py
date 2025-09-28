import logging
from logging.handlers import RotatingFileHandler

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
        logger.addHandler(handler)
        logger.propagate = False

        return logger


bot_logger = BotLogger.setup_logger()
