from pathlib import Path

from src.config import BASE_DIR
from src.interfaces.bot.i18n import DEFAULT_LOCALE, normalize_locale

DATA_PATH = Path(BASE_DIR / "interfaces" / "bot" / "data")


def _read_localized_markdown(file_name: str, locale: str | None = None) -> str:
    normalized_locale = normalize_locale(locale)

    localized_file_path = DATA_PATH / normalized_locale / file_name
    if localized_file_path.exists():
        with open(localized_file_path, mode="r", encoding="utf-8") as file:
            return file.read()

    default_localized_file_path = DATA_PATH / DEFAULT_LOCALE / file_name
    if default_localized_file_path.exists():
        with open(default_localized_file_path, mode="r", encoding="utf-8") as file:
            return file.read()

    fallback_file_path = DATA_PATH / file_name
    with open(fallback_file_path, mode="r", encoding="utf-8") as file:
        return file.read()


def load_stack(locale: str | None = None) -> str:
    return _read_localized_markdown(file_name="stack.md", locale=locale)


def load_about_me(locale: str | None = None) -> str:
    return _read_localized_markdown(file_name="about_me.md", locale=locale)


def load_resume(locale: str | None = None) -> str:
    return _read_localized_markdown(file_name="cv.md", locale=locale)
