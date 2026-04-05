import warnings
from datetime import UTC, datetime
from time import perf_counter

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, InlineKeyboardMarkup,
                           InlineKeyboardButton, CallbackQuery,
                           KeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from src.application.memory import MemoryService
from src.config import settings
from src.domain.memory.entities import MemoryQuota
from src.infrastructure.gpt.yandex_client import ask_yandex_gpt
from src.infrastructure.postgres.memory_repository import PostgresMemoryRepository
from src.infrastructure.postgres.session import session_scope
from src.interfaces.bot.bot_logging import log_event
from src.interfaces.bot.keyboards.main import get_main_menu_keyboard
from src.interfaces.bot.metrics import bot_metrics
from src.interfaces.bot.services.load_resume import load_stack, load_about_me
from ..constants import COMMANDS_WITH_DESCRIPTION
from ..bot_logging import bot_logger

warnings.filterwarnings("ignore",
                        category=SyntaxWarning,
                        message="invalid escape sequence")
router = Router()
COMMANDS_BLOCK = f"*Доступные команды:*\n{COMMANDS_WITH_DESCRIPTION}"


class ChatMode(StatesGroup):
    talking_to_ai = State()


def _create_memory_service(repository: PostgresMemoryRepository) -> MemoryService:
    return MemoryService(
        repository=repository,
        user_message_limit=settings.MEMORY_USER_MESSAGE_LIMIT,
        window_minutes=settings.MEMORY_LIMIT_WINDOW_MINUTES,
        recent_messages_limit=settings.MEMORY_RECENT_MESSAGES,
        search_results_limit=settings.MEMORY_SEARCH_RESULTS,
        summary_trigger_messages=settings.MEMORY_SUMMARY_TRIGGER_MESSAGES,
        summary_source_messages=settings.MEMORY_SUMMARY_SOURCE_MESSAGES,
    )


def _seconds_until(blocked_until: datetime | None) -> int:
    if blocked_until is None:
        return 0
    now_utc = datetime.now(UTC)
    return max(0, int((blocked_until - now_utc).total_seconds()))


def _format_countdown(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_quota_message(quota: MemoryQuota) -> str:
    remaining = max(0, quota.limit - quota.used)
    if quota.allowed:
        return (
            "✅ Лимит активен\\.\n"
            f"Использовано: {quota.used}/{quota.limit}\n"
            f"Осталось: {remaining}\n"
            f"Окно: {settings.MEMORY_LIMIT_WINDOW_MINUTES} минут\\."
        )

    seconds_until_reset = _seconds_until(quota.blocked_until)
    countdown = _format_countdown(seconds_until_reset)
    return (
        "⛔ Лимит достигнут\\.\n"
        f"Использовано: {quota.used}/{quota.limit}\n"
        f"Следующий сброс через: {countdown}\n"
        f"Окно: {settings.MEMORY_LIMIT_WINDOW_MINUTES} минут\\."
    )


def _classify_gpt_error(error: Exception) -> str:
    message = str(error)
    if "StatusCode.UNAUTHENTICATED" in message or "Unknown api key" in message:
        return "auth"
    if "StatusCode.DEADLINE_EXCEEDED" in message or "timeout" in message.lower():
        return "timeout"
    if "StatusCode.RESOURCE_EXHAUSTED" in message:
        return "rate_limit"
    return "unknown"


@router.message(Command("start"))
async def start_command(message: Message):
    name = message.from_user.first_name
    bot_logger.info(f"User <{message.from_user.username}> used your /start")
    ai_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💬 Поговорить с ИИ о резюмe",
            callback_data="talk_to_ai")]
    ])
    await message.answer(
        f"*Привет, {name}👋*\n"
        "Я бот Кирилла🤖\n\n"
        "Помогу быстро узнать обо мне и отвечу на вопросы по резюме 💼\n"
        "Чтобы начать диалог, нажми *Поговорить с ИИ о резюме* ниже\\.\n\n"
        f"{COMMANDS_BLOCK}\n\n"
        "⏱️ Лимит ИИ\\-чата: "
        f"{settings.MEMORY_USER_MESSAGE_LIMIT} сообщений "
        f"за {settings.MEMORY_LIMIT_WINDOW_MINUTES} минут\\!❗",
        reply_markup=ai_button,
    )
    await message.answer(
        "Быстрые команды всегда под рукой 👇",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("about_kirill"))
async def start_command(message: Message):
    bot_logger.info(f"User <{message.from_user.username}> used your /about_kirill")
    await message.answer(
        load_about_me(),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("short_stack"))
async def short_stack_command(message: Message):
    bot_logger.info(f"User <{message.from_user.username}> used your /short_stack")
    await message.answer(
        load_stack(),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    user_message = (
        "✨ Вот как я могу помочь:\n\n"
        f"{COMMANDS_BLOCK}\n\n"
        "Хочешь пообщаться с ИИ по резюме? Нажми /start и выбери кнопку 💬"
    )
    await message.answer(user_message, reply_markup=get_main_menu_keyboard())


@router.message(Command("quota"))
async def quota_command(message: Message):
    if not message.from_user:
        await message.answer("Не удалось определить пользователя\\.")
        return

    user_id = message.from_user.id
    username = message.from_user.username
    try:
        async with session_scope() as session:
            repository = PostgresMemoryRepository(session)
            service = _create_memory_service(repository)
            await service.ensure_user(user_id=user_id, username=username)
            quota = await service.check_quota(user_id=user_id)
    except RuntimeError as err:
        bot_logger.error("Memory storage configuration error: %s", err)
        await message.answer("Ошибка конфигурации памяти\\. Проверьте DATABASE\\_URL\\.")
        return
    except Exception:
        bot_logger.exception("Failed to get quota info")
        await message.answer("Не удалось получить информацию о лимите\\.")
        return

    log_event(
        "quota_status",
        user_id=user_id,
        username=username,
        used=quota.used,
        limit=quota.limit,
        allowed=quota.allowed,
        reset_in_seconds=_seconds_until(quota.blocked_until),
    )
    await message.answer(_format_quota_message(quota), reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "talk_to_ai")
async def talk_to_ai_handler(callback: CallbackQuery, state: FSMContext):
    stop_button = KeyboardButton(text="❌ Остановить разговор с ИИ")
    builder = ReplyKeyboardBuilder()
    builder.row(stop_button)
    stop_keyboard = builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Введите свой вопрос..."
    )
    await callback.message.answer(
        "Супер, начинаем диалог 👨‍💼\n\n"
        "Напиши любой вопрос по резюме, и я отвечу как кандидат\\.\n"
        "Чтобы выйти из режима ИИ, нажми кнопку ❌\n\n"
        f"{COMMANDS_BLOCK}",
        reply_markup=stop_keyboard
    )
    await state.set_state(ChatMode.talking_to_ai)
    await callback.answer(text="Вы начали разговор с ИИ")


@router.message(F.text == "❌ Остановить разговор с ИИ")
async def stop_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "ИИ\\-режим отключён\\!\n\n"
        "Можно снова начать в любой момент через /start 💬\n\n"
        f"{COMMANDS_BLOCK}",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(
    ChatMode.talking_to_ai,
    flags={"chat_action": "typing", "rate_limit": 7})
async def handle_ai_question(message: Message):
    if not message.from_user:
        await message.reply("Пользователь не определён\\.")
        return

    started_at = perf_counter()
    user_id = message.from_user.id
    username = message.from_user.username
    if not message.text:
        await message.reply("Пожалуйста, отправьте текстовый вопрос 💬")
        return
    question_text = message.text

    # Read transaction: user, quota, retrieval context
    try:
        async with session_scope() as session:
            memory_repository = PostgresMemoryRepository(session)
            memory_service = _create_memory_service(memory_repository)
            await memory_service.ensure_user(user_id=user_id, username=username)

            quota = await memory_service.check_quota(user_id=user_id)
            log_event(
                "quota_decision",
                user_id=user_id,
                username=username,
                used=quota.used,
                limit=quota.limit,
                allowed=quota.allowed,
                reset_in_seconds=_seconds_until(quota.blocked_until),
            )
            if not quota.allowed:
                response_ms = round((perf_counter() - started_at) * 1000, 2)
                bot_metrics.record_quota_blocked()
                bot_metrics.record_request(latency_ms=response_ms, success=True)
                metrics = bot_metrics.snapshot()
                log_event(
                    "ai_request_blocked",
                    user_id=user_id,
                    username=username,
                    latency_ms=response_ms,
                    requests_total=metrics.requests_total,
                    failures_total=metrics.failures_total,
                    quota_blocked_total=metrics.quota_blocked_total,
                    avg_response_ms=metrics.avg_response_ms,
                    p95_response_ms=metrics.p95_response_ms,
                )
                await message.reply(_format_quota_message(quota))
                return

            context = await memory_service.build_context(
                user_id=user_id,
                question=question_text,
            )
            memory_context = memory_service.format_context(context)
    except RuntimeError as err:
        bot_logger.error("Memory storage configuration error: %s", err)
        await message.reply("Ошибка конфигурации памяти\\. Проверьте DATABASE\\_URL\\.")
        return
    except Exception:
        response_ms = round((perf_counter() - started_at) * 1000, 2)
        bot_metrics.record_request(latency_ms=response_ms, success=False)
        metrics = bot_metrics.snapshot()
        log_event(
            "ai_request_failed",
            user_id=user_id,
            username=username,
            stage="read_context",
            error_category="database",
            latency_ms=response_ms,
            requests_total=metrics.requests_total,
            failures_total=metrics.failures_total,
            quota_blocked_total=metrics.quota_blocked_total,
            avg_response_ms=metrics.avg_response_ms,
            p95_response_ms=metrics.p95_response_ms,
        )
        bot_logger.exception("Failed to read memory context")
        await message.reply("Не удалось обработать сообщение\\. Попробуйте снова позже\\.")
        return

    # GPT call outside DB transaction
    try:
        reply = await ask_yandex_gpt(question_text, memory_context=memory_context)
    except Exception as error:
        response_ms = round((perf_counter() - started_at) * 1000, 2)
        bot_metrics.record_request(latency_ms=response_ms, success=False)
        metrics = bot_metrics.snapshot()
        log_event(
            "ai_request_failed",
            user_id=user_id,
            username=username,
            stage="gpt_call",
            error_category=_classify_gpt_error(error),
            latency_ms=response_ms,
            requests_total=metrics.requests_total,
            failures_total=metrics.failures_total,
            quota_blocked_total=metrics.quota_blocked_total,
            avg_response_ms=metrics.avg_response_ms,
            p95_response_ms=metrics.p95_response_ms,
        )
        bot_logger.exception("Failed to call GPT model")
        await message.reply("Не удалось обработать сообщение\\. Попробуйте снова позже\\.")
        return

    # Write transaction: persist dialogue and refresh summary
    try:
        async with session_scope() as session:
            memory_repository = PostgresMemoryRepository(session)
            memory_service = _create_memory_service(memory_repository)
            await memory_service.save_turn(
                user_id=user_id,
                user_text=question_text,
                assistant_reply=reply,
            )
            summary = await memory_service.update_summary_if_needed(user_id=user_id)
    except RuntimeError as err:
        bot_logger.error("Memory storage configuration error: %s", err)
        await message.reply("Ошибка конфигурации памяти\\. Проверьте DATABASE\\_URL\\.")
        return
    except Exception:
        response_ms = round((perf_counter() - started_at) * 1000, 2)
        bot_metrics.record_request(latency_ms=response_ms, success=False)
        metrics = bot_metrics.snapshot()
        log_event(
            "ai_request_failed",
            user_id=user_id,
            username=username,
            stage="save_memory",
            error_category="database",
            latency_ms=response_ms,
            requests_total=metrics.requests_total,
            failures_total=metrics.failures_total,
            quota_blocked_total=metrics.quota_blocked_total,
            avg_response_ms=metrics.avg_response_ms,
            p95_response_ms=metrics.p95_response_ms,
        )
        bot_logger.exception("Failed to save turn or update summary")
        await message.reply("Не удалось сохранить контекст диалога\\. Попробуйте снова позже\\.")
        return

    response_ms = round((perf_counter() - started_at) * 1000, 2)
    bot_metrics.record_request(latency_ms=response_ms, success=True)
    metrics = bot_metrics.snapshot()
    log_event(
        "ai_request_success",
        user_id=user_id,
        username=username,
        used=quota.used + 1,
        limit=quota.limit,
        summary_updated=summary is not None,
        latency_ms=response_ms,
        requests_total=metrics.requests_total,
        failures_total=metrics.failures_total,
        quota_blocked_total=metrics.quota_blocked_total,
        avg_response_ms=metrics.avg_response_ms,
        p95_response_ms=metrics.p95_response_ms,
    )
    bot_logger.info(f"User <{username}> used AI feature")
    try:
        await message.reply(f"`{reply}`")
    except TelegramBadRequest:
        await message.reply(reply)


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    bot_logger.info(
        f"User <{message.from_user.username}> "
        f"wrote unreachable message: {message.text} ")
    current_state = await state.get_state()
    if current_state == ChatMode.talking_to_ai:
        return

    await message.reply(
        "🤔 Я не понял это сообщение\\.\n\n"
        "Выбери команду ниже, и я подскажу дальше 👇\n\n"
        f"{COMMANDS_BLOCK}\n\n"
        "Для быстрого старта ИИ\\-диалога используй /start 💬",
        reply_markup=get_main_menu_keyboard(),
    )
