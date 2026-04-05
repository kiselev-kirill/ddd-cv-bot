FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install "poetry>=2.1,<3.0"

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --only main

COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY src /app/src

CMD ["python", "-m", "src.interfaces.bot.bot"]
