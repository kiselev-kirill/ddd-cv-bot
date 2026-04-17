from typing import Final

DEFAULT_LOCALE: Final[str] = "ru"
SUPPORTED_LOCALES: Final[set[str]] = {"ru", "en"}

TRANSLATIONS: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "commands.title": "Доступные команды:",
        "bot_command.start": "Главное меню и запуск ИИ чата",
        "bot_command.about_kirill": "Коротко обо мне",
        "bot_command.short_stack": "Мой стек в 1 минуту",
        "bot_command.quota": "Текущий лимит ИИ сообщений",
        "bot_command.help": "Все команды бота",
        "command_block.start": "главное меню и запуск ИИ чата",
        "command_block.about_kirill": "коротко обо мне",
        "command_block.short_stack": "мой стек в 1 минуту",
        "command_block.quota": "остаток сообщений в лимите",
        "command_block.help": "все команды бота",
        "start.talk_button": "💬 Поговорить с ИИ о резюме",
        "start.greeting": "Привет, {name} 👋",
        "start.intro_1": "Я бот Кирилла 🤖",
        "start.intro_2": "Помогу быстро узнать обо мне и отвечу на вопросы по резюме 💼",
        "start.intro_3": "Чтобы начать диалог, нажми «Поговорить с ИИ о резюме» ниже.",
        "start.limit": "Лимит ИИ-чата: {limit} сообщений за {minutes} минут.",
        "start.quick_commands": "Быстрые команды всегда под рукой 👇",
        "about.memory_config_error": "Ошибка конфигурации памяти. Проверьте DATABASE_URL.",
        "help.intro": "Вот как я могу помочь:",
        "help.ai_hint": "Хочешь пообщаться с ИИ по резюме? Нажми /start и выбери кнопку 💬",
        "quota.user_not_defined": "Не удалось определить пользователя.",
        "quota.active": "✅ Лимит активен.",
        "quota.reached": "⛔ Лимит достигнут.",
        "quota.used": "Использовано: {used}/{limit}",
        "quota.remaining": "Осталось: {remaining}",
        "quota.next_reset": "Следующий сброс через: {countdown}",
        "quota.window": "Окно: {minutes} минут.",
        "quota.fetch_error": "Не удалось получить информацию о лимите.",
        "talk.started": "Супер, начинаем диалог 👨‍💼",
        "talk.prompt": "Напиши любой вопрос по резюме, и я отвечу как кандидат.",
        "talk.exit_hint": "Чтобы выйти из режима ИИ, нажми кнопку ❌",
        "talk.started_callback": "Вы начали разговор с ИИ",
        "talk.stop_button": "❌ Остановить разговор с ИИ",
        "talk.stop_placeholder": "Введите свой вопрос...",
        "talk.stopped": "ИИ-режим отключён!",
        "talk.stopped_hint": "Можно снова начать в любой момент через /start 💬",
        "ai.user_not_defined": "Пользователь не определён.",
        "ai.text_only": "Пожалуйста, отправьте текстовый вопрос 💬",
        "ai.processing_error": "Не удалось обработать сообщение. Попробуйте снова позже.",
        "ai.save_context_error": "Не удалось сохранить контекст диалога. Попробуйте снова позже.",
        "fallback.unknown": "🤔 Я не понял это сообщение.",
        "fallback.choose_command": "Выбери команду ниже, и я подскажу дальше 👇",
        "fallback.ai_hint": "Для быстрого старта ИИ-диалога используй /start 💬",
        "keyboard.placeholder": "Выберите команду 👇",
        "gpt.system_header": "Ты — кандидат. Вот его резюме:",
        "gpt.memory_header": "Контекст прошлых диалогов с пользователем:",
        "gpt.language_instruction": "Отвечай строго на русском языке.",
    },
    "en": {
        "commands.title": "Available commands:",
        "bot_command.start": "Main menu and start AI chat",
        "bot_command.about_kirill": "Short intro about me",
        "bot_command.short_stack": "My stack in 1 minute",
        "bot_command.quota": "Current AI message limit",
        "bot_command.help": "All bot commands",
        "command_block.start": "main menu and start AI chat",
        "command_block.about_kirill": "short intro about me",
        "command_block.short_stack": "my stack in 1 minute",
        "command_block.quota": "remaining messages in the limit window",
        "command_block.help": "all bot commands",
        "start.talk_button": "💬 Talk to AI about CV",
        "start.greeting": "Hi, {name} 👋",
        "start.intro_1": "I am Kirill's bot 🤖",
        "start.intro_2": "I can quickly tell you about me and answer CV questions 💼",
        "start.intro_3": "To start chatting, tap “Talk to AI about CV” below.",
        "start.limit": "AI chat limit: {limit} messages per {minutes} minutes.",
        "start.quick_commands": "Quick commands are always below 👇",
        "about.memory_config_error": "Memory configuration error. Check DATABASE_URL.",
        "help.intro": "Here is how I can help:",
        "help.ai_hint": "Want to chat with AI about the CV? Press /start and tap the button 💬",
        "quota.user_not_defined": "Could not identify the user.",
        "quota.active": "✅ Limit is active.",
        "quota.reached": "⛔ Limit reached.",
        "quota.used": "Used: {used}/{limit}",
        "quota.remaining": "Remaining: {remaining}",
        "quota.next_reset": "Next reset in: {countdown}",
        "quota.window": "Window: {minutes} minutes.",
        "quota.fetch_error": "Could not fetch quota information.",
        "talk.started": "Great, let's start 👨‍💼",
        "talk.prompt": "Ask any question about the CV, and I will answer as the candidate.",
        "talk.exit_hint": "To leave AI mode, press the ❌ button.",
        "talk.started_callback": "AI chat started",
        "talk.stop_button": "❌ Stop AI chat",
        "talk.stop_placeholder": "Type your question...",
        "talk.stopped": "AI mode is off.",
        "talk.stopped_hint": "You can start again anytime with /start 💬",
        "ai.user_not_defined": "User is not defined.",
        "ai.text_only": "Please send a text question 💬",
        "ai.processing_error": "Failed to process the message. Please try again later.",
        "ai.save_context_error": "Failed to save chat context. Please try again later.",
        "fallback.unknown": "🤔 I did not understand this message.",
        "fallback.choose_command": "Choose a command below and I will guide you 👇",
        "fallback.ai_hint": "For a quick AI chat start, use /start 💬",
        "keyboard.placeholder": "Choose a command 👇",
        "gpt.system_header": "You are the candidate. Here is the CV:",
        "gpt.memory_header": "Context from previous user chats:",
        "gpt.language_instruction": "Reply strictly in English.",
    },
}


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE

    normalized = locale.strip().lower().replace("_", "-")
    if normalized.startswith("ru"):
        return "ru"
    if normalized.startswith("en"):
        return "en"
    return DEFAULT_LOCALE


def t(locale: str | None, key: str, **kwargs: object) -> str:
    normalized_locale = normalize_locale(locale)
    locale_map = TRANSLATIONS.get(normalized_locale, TRANSLATIONS[DEFAULT_LOCALE])
    template = locale_map.get(key, TRANSLATIONS[DEFAULT_LOCALE].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
