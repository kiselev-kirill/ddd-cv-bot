from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="/start"), KeyboardButton(text="/help"))
    builder.row(
        KeyboardButton(text="/about_kirill"),
        KeyboardButton(text="/short_stack"),
    )
    builder.row(KeyboardButton(text="/quota"))
    return builder.as_markup(
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите команду 👇",
    )
