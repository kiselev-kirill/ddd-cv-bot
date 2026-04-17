from typing import Final

from src.interfaces.bot.i18n import t

_COMMAND_SPECS: Final[
    tuple[tuple[str, str, str, str, str], ...]
] = (
    ("start", "start", "🏠", "bot_command.start", "command_block.start"),
    (
        "about_kirill",
        "about_kirill",
        "👤",
        "bot_command.about_kirill",
        "command_block.about_kirill",
    ),
    (
        "short_stack",
        "short_stack",
        "🛠️",
        "bot_command.short_stack",
        "command_block.short_stack",
    ),
    ("quota", "quota", "⏱️", "bot_command.quota", "command_block.quota"),
    ("help", "help", "❓", "bot_command.help", "command_block.help"),
)


def get_bot_commands(locale: str) -> tuple[tuple[str, str], ...]:
    return tuple((command, t(locale, description_key))
                 for command, _, _, description_key, _ in _COMMAND_SPECS)


def get_commands_with_description(locale: str) -> str:
    lines = [
        f"{emoji} /{command_display} - {t(locale, block_description_key)}"
        for _, command_display, emoji, _, block_description_key in _COMMAND_SPECS
    ]
    return "\n".join(lines)
