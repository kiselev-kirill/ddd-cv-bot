# DDD CV Bot

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Alembic](https://img.shields.io/badge/Migrations-Alembic-black)

Telegram bot that presents Kirill's CV and answers recruiter questions with `YandexGPT`, while keeping per-user conversational memory in PostgreSQL.

## What This Bot Does

- Serves static profile content via commands (`/about_kirill`, `/short_stack`).
- Starts an AI chat mode focused on CV/resume Q&A.
- Applies per-user quota limits (messages per time window).
- Stores conversation history and builds compact rolling summaries.
- Uses PostgreSQL full-text search to retrieve relevant past messages.
- Writes structured logs and in-memory request metrics.

## Architecture

This project follows layered organization close to DDD/Clean Architecture:

- `interfaces` - Telegram handlers, middleware, keyboards.
- `application` - orchestration logic (`MemoryService`).
- `domain` - entities/repository contracts.
- `infrastructure` - PostgreSQL repository + Yandex GPT client.

```mermaid
flowchart LR
    U[Telegram User] --> H[aiogram Handler]
    H --> M1[MemoryService: ensure user + quota + context]
    M1 --> R[(PostgreSQL)]
    M1 --> G[YandexGPT]
    G --> H
    H --> M2[MemoryService: save turn + maybe summary]
    M2 --> R
```

## Quick Start (Docker Compose)

### 1. Create `.env`

Minimal setup:

```env
# Required for bot runtime
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# Optional: route Telegram API requests through HTTP/SOCKS proxy
# Example: socks5://user:pass@172.17.0.1:10000
TELEGRAM_PROXY_URL=
YANDEX_GPT_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_yandex_folder_id

# Optional prompt customization
GPT_PROMPT=Отвечай кратко, как кандидат по резюме.

# Optional (currently not used in code path)
YANDEX_ID_KEY=

# PostgreSQL settings for docker-compose
POSTGRES_DB=cv_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432

# Optional image name
BOT_IMAGE=ddd-cv-bot:latest
```

### 2. Run everything

```bash
docker compose up --build
```

`docker-compose` starts:

- `db` (PostgreSQL 16)
- `migrate` (runs `alembic upgrade head`)
- `bot` (starts polling loop)

### 3. Check logs

```bash
docker compose logs -f bot
```

## Local Development (Poetry)

### Prerequisites

- Python `3.13`
- Poetry `2.1+`
- PostgreSQL `16+`

### Setup

```bash
poetry install
```

Create `.env` and include at least:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_PROXY_URL=
YANDEX_GPT_API_KEY=...
YANDEX_FOLDER_ID=...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cv_bot
```

Apply migrations and run:

```bash
poetry run alembic upgrade head
poetry run python -m src.interfaces.bot.bot
```

## Configuration Reference

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram Bot API token |
| `TELEGRAM_PROXY_URL` | No | `None` | Optional HTTP/SOCKS proxy URL for Telegram API (`http://...` or `socks5://...`) |
| `YANDEX_GPT_API_KEY` | Yes | - | Yandex Cloud ML auth key |
| `YANDEX_FOLDER_ID` | Yes | - | Yandex Cloud folder id |
| `DATABASE_URL` | Yes (local run) | `""` | Async SQLAlchemy DSN (`postgresql+asyncpg://...`) |
| `GPT_PROMPT` | No | `""` | Extra system prompt text appended to model context |
| `YANDEX_ID_KEY` | No | `None` | Present in config, currently not used |
| `MEMORY_USER_MESSAGE_LIMIT` | No | `5` | Max user messages per window |
| `MEMORY_LIMIT_WINDOW_MINUTES` | No | `60` | Quota window duration |
| `MEMORY_RECENT_MESSAGES` | No | `8` | Recent chat messages sent to context |
| `MEMORY_SEARCH_RESULTS` | No | `5` | Relevant older messages from search |
| `MEMORY_SUMMARY_TRIGGER_MESSAGES` | No | `12` | New messages needed before summary refresh |
| `MEMORY_SUMMARY_SOURCE_MESSAGES` | No | `40` | Max messages considered for summary build |
| `POSTGRES_DB` | No | `cv_bot` | Docker Compose database name |
| `POSTGRES_USER` | No | `postgres` | Docker Compose database user |
| `POSTGRES_PASSWORD` | No | `postgres` | Docker Compose database password |
| `POSTGRES_PORT` | No | `5432` | Host port for PostgreSQL |
| `BOT_IMAGE` | No | `ddd-cv-bot:latest` | Docker image tag used by compose |

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Main menu + AI chat entry point |
| `/about_kirill` | Short profile |
| `/short_stack` | Tech stack overview |
| `/quota` | Current AI message quota status |
| `/help` | Commands help |

## Memory and Quota Logic

For each AI question (in chat mode):

1. Ensure user record exists in `bot_users`.
2. Check quota by counting `role='user'` messages in the active time window.
3. Build GPT context from:
   - latest summary (`conversation_summaries`)
   - recent messages
   - relevant older messages (PostgreSQL FTS via `tsvector` + GIN index)
4. Call `YandexGPT` with:
   - resume content (`src/interfaces/bot/data/cv.md`)
   - `GPT_PROMPT`
   - memory context
5. Save user + assistant messages.
6. Refresh rolling summary when threshold is reached.

Additionally, a middleware-level anti-spam throttle applies to AI questions (`rate_limit=7` seconds).

## Content Files (Your CV Data)

The bot serves and injects markdown content from:

- `src/interfaces/bot/data/about_me.md`
- `src/interfaces/bot/data/stack.md`
- `src/interfaces/bot/data/cv.md`

If you customize the bot for another person, replace these files first.

## Database Schema

Alembic revisions:

- `bot_users` - Telegram user identity and timestamps.
- `conversation_messages` - dialogue turns with role/content and FTS index.
- `conversation_summaries` - rolling conversation summaries with `max_message_id`.

## Useful Commands

```bash
# run latest migrations
poetry run alembic upgrade head

# create new migration
poetry run alembic revision --autogenerate -m "describe_change"

# run only database in docker
docker compose up -d db

# rerun migration container
docker compose run --rm migrate
```

## Logging and Observability

- File logger: `src/bot.log` (rotating, max ~5 MB x 3 backups).
- Structured JSON events include:
  - `quota_status`
  - `quota_decision`
  - `ai_request_success`
  - `ai_request_failed`
  - `ai_request_blocked`
- In-memory metrics tracked:
  - total requests
  - failures
  - quota-blocked count
  - avg/p95 latency

## Troubleshooting

- `DATABASE_URL is not configured`
  - Set `DATABASE_URL` in `.env` (for local runs), or use Docker Compose where it is injected.
- GPT auth errors (`UNAUTHENTICATED`, `Unknown api key`)
  - Verify `YANDEX_GPT_API_KEY` and `YANDEX_FOLDER_ID`.
- Bot starts but does not answer AI questions
  - Confirm `/start` -> "Поговорить с ИИ" flow is active; AI handler works only in chat state.
- Frequent "Слишком быстро, тигр🐯"
  - You are hitting middleware rate limiting for AI chat messages.

## Current Gaps

- No automated test suite in repository yet.
- CI workflow file exists but is currently empty.
