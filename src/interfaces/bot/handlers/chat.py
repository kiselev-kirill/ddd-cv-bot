import warnings
from datetime import UTC, datetime
from time import perf_counter

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.application.memory import MemoryService
from src.config import settings
from src.domain.memory.entities import MemoryQuota
from src.infrastructure.gpt.yandex_client import ask_yandex_gpt
from src.infrastructure.postgres.memory_repository import PostgresMemoryRepository
from src.infrastructure.postgres.session import session_scope
from src.interfaces.bot.bot_logging import log_event
from src.interfaces.bot.bot_logging import bot_logger
from src.interfaces.bot.constants import get_commands_with_description
from src.interfaces.bot.i18n import DEFAULT_LOCALE, normalize_locale, t
from src.interfaces.bot.keyboards.main import get_main_menu_keyboard
from src.interfaces.bot.metrics import bot_metrics
from src.interfaces.bot.services.telegram_format import render_markdown_to_html
from src.interfaces.bot.services.load_resume import load_about_me, load_stack

warnings.filterwarnings(
    "ignore",
    category=SyntaxWarning,
    message="invalid escape sequence",
)
router = Router()
STOP_AI_TEXTS = (t("ru", "talk.stop_button"), t("en", "talk.stop_button"))


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


def _locale_from_message(message: Message) -> str:
    if not message.from_user:
        return DEFAULT_LOCALE
    return normalize_locale(message.from_user.language_code)


def _locale_from_callback(callback: CallbackQuery) -> str:
    if not callback.from_user:
        return DEFAULT_LOCALE
    return normalize_locale(callback.from_user.language_code)


def _commands_block(locale: str) -> str:
    return (
        f"{t(locale, 'commands.title')}\n"
        f"{get_commands_with_description(locale)}"
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


def _format_quota_message(quota: MemoryQuota, locale: str) -> str:
    remaining = max(0, quota.limit - quota.used)
    if quota.allowed:
        return "\n".join(
            (
                t(locale, "quota.active"),
                t(locale, "quota.used", used=quota.used, limit=quota.limit),
                t(locale, "quota.remaining", remaining=remaining),
                t(
                    locale,
                    "quota.window",
                    minutes=settings.MEMORY_LIMIT_WINDOW_MINUTES,
                ),
            )
        )

    seconds_until_reset = _seconds_until(quota.blocked_until)
    countdown = _format_countdown(seconds_until_reset)
    return "\n".join(
        (
            t(locale, "quota.reached"),
            t(locale, "quota.used", used=quota.used, limit=quota.limit),
            t(locale, "quota.next_reset", countdown=countdown),
            t(locale, "quota.window", minutes=settings.MEMORY_LIMIT_WINDOW_MINUTES),
        )
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
    locale = _locale_from_message(message)
    name = message.from_user.first_name if message.from_user else (
        "друг" if locale == "ru" else "friend"
    )
    username = message.from_user.username if message.from_user else None
    bot_logger.info("User <%s> used your /start", username)
    ai_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(locale, "start.talk_button"),
                    callback_data="talk_to_ai",
                )
            ]
        ]
    )
    await message.answer(
        "\n".join(
            (
                t(locale, "start.greeting", name=name),
                t(locale, "start.intro_1"),
                "",
                t(locale, "start.intro_2"),
                t(locale, "start.intro_3"),
                "",
                _commands_block(locale),
                "",
                t(
                    locale,
                    "start.limit",
                    limit=settings.MEMORY_USER_MESSAGE_LIMIT,
                    minutes=settings.MEMORY_LIMIT_WINDOW_MINUTES,
                ),
            )
        ),
        reply_markup=ai_button,
        parse_mode=None,
    )
    await message.answer(
        t(locale, "start.quick_commands"),
        reply_markup=get_main_menu_keyboard(locale),
        parse_mode=None,
    )


@router.message(Command("about_kirill"))
async def about_kirill_command(message: Message):
    locale = _locale_from_message(message)
    username = message.from_user.username if message.from_user else None
    bot_logger.info("User <%s> used your /about_kirill", username)
    await message.answer(
        render_markdown_to_html(load_about_me(locale)),
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(locale),
    )


@router.message(Command("short_stack"))
async def short_stack_command(message: Message):
    locale = _locale_from_message(message)
    username = message.from_user.username if message.from_user else None
    bot_logger.info("User <%s> used your /short_stack", username)
    await message.answer(
        render_markdown_to_html(load_stack(locale)),
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(locale),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    locale = _locale_from_message(message)
    user_message = "\n".join(
        (
            f"✨ {t(locale, 'help.intro')}",
            "",
            _commands_block(locale),
            "",
            t(locale, "help.ai_hint"),
        )
    )
    await message.answer(
        user_message,
        reply_markup=get_main_menu_keyboard(locale),
        parse_mode=None,
    )


@router.message(Command("quota"))
async def quota_command(message: Message):
    locale = _locale_from_message(message)
    if not message.from_user:
        await message.answer(t(locale, "quota.user_not_defined"), parse_mode=None)
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
        await message.answer(t(locale, "about.memory_config_error"), parse_mode=None)
        return
    except Exception:
        bot_logger.exception("Failed to get quota info")
        await message.answer(t(locale, "quota.fetch_error"), parse_mode=None)
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
    await message.answer(
        _format_quota_message(quota, locale),
        reply_markup=get_main_menu_keyboard(locale),
        parse_mode=None,
    )


@router.callback_query(F.data == "talk_to_ai")
async def talk_to_ai_handler(callback: CallbackQuery, state: FSMContext):
    locale = _locale_from_callback(callback)
    stop_button = KeyboardButton(text=t(locale, "talk.stop_button"))
    builder = ReplyKeyboardBuilder()
    builder.row(stop_button)
    stop_keyboard = builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder=t(locale, "talk.stop_placeholder"),
    )
    if callback.message:
        await callback.message.answer(
            "\n".join(
                (
                    t(locale, "talk.started"),
                    "",
                    t(locale, "talk.prompt"),
                    t(locale, "talk.exit_hint"),
                    "",
                    _commands_block(locale),
                )
            ),
            reply_markup=stop_keyboard,
            parse_mode=None,
        )
    await state.set_state(ChatMode.talking_to_ai)
    await callback.answer(text=t(locale, "talk.started_callback"))


@router.message(F.text.in_(STOP_AI_TEXTS))
async def stop_ai_chat(message: Message, state: FSMContext):
    locale = _locale_from_message(message)
    await state.clear()
    await message.answer(
        "\n".join(
            (
                t(locale, "talk.stopped"),
                "",
                t(locale, "talk.stopped_hint"),
                "",
                _commands_block(locale),
            )
        ),
        reply_markup=get_main_menu_keyboard(locale),
        parse_mode=None,
    )


@router.message(
    ChatMode.talking_to_ai,
    flags={"chat_action": "typing", "rate_limit": 7},
)
async def handle_ai_question(message: Message):
    locale = _locale_from_message(message)
    if not message.from_user:
        await message.reply(t(locale, "ai.user_not_defined"), parse_mode=None)
        return

    started_at = perf_counter()
    user_id = message.from_user.id
    username = message.from_user.username
    if not message.text:
        await message.reply(t(locale, "ai.text_only"), parse_mode=None)
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
                await message.reply(_format_quota_message(quota, locale), parse_mode=None)
                return

            context = await memory_service.build_context(
                user_id=user_id,
                question=question_text,
            )
            memory_context = memory_service.format_context(context)
    except RuntimeError as err:
        bot_logger.error("Memory storage configuration error: %s", err)
        await message.reply(t(locale, "about.memory_config_error"), parse_mode=None)
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
        await message.reply(t(locale, "ai.processing_error"), parse_mode=None)
        return

    # GPT call outside DB transaction
    try:
        reply = await ask_yandex_gpt(
            question_text,
            memory_context=memory_context,
            locale=locale,
        )
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
        await message.reply(t(locale, "ai.processing_error"), parse_mode=None)
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
        await message.reply(t(locale, "about.memory_config_error"), parse_mode=None)
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
        await message.reply(t(locale, "ai.save_context_error"), parse_mode=None)
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
    bot_logger.info("User <%s> used AI feature", username)
    try:
        await message.reply(f"`{reply}`")
    except TelegramBadRequest:
        await message.reply(reply, parse_mode=None)


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    locale = _locale_from_message(message)
    username = message.from_user.username if message.from_user else None
    bot_logger.info("User <%s> wrote unreachable message: %s", username, message.text)
    current_state = await state.get_state()
    if current_state == ChatMode.talking_to_ai:
        return

    await message.reply(
        "\n".join(
            (
                t(locale, "fallback.unknown"),
                "",
                t(locale, "fallback.choose_command"),
                "",
                _commands_block(locale),
                "",
                t(locale, "fallback.ai_hint"),
            )
        ),
        reply_markup=get_main_menu_keyboard(locale),
        parse_mode=None,
    )
