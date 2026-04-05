from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.memory.entities import MemoryMessage, MemorySummary
from src.domain.memory.repository import AbstractMemoryRepository
from src.infrastructure.postgres.tables import (
    BotUserORM,
    ConversationMessageORM,
    ConversationSummaryORM,
)


class PostgresMemoryRepository(AbstractMemoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_user(self, user_id: int, username: str | None) -> None:
        stmt = (
            insert(BotUserORM)
            .values(
                id=user_id,
                username=username,
            )
            .on_conflict_do_update(
                index_elements=[BotUserORM.id],
                set_={
                    "username": username,
                    "updated_at": func.now(),
                },
            )
        )
        await self._session.execute(stmt)

    async def add_message(self, user_id: int, role: str, content: str) -> MemoryMessage:
        row = ConversationMessageORM(
            user_id=user_id,
            role=role,
            content=content,
        )
        self._session.add(row)
        await self._session.flush()
        if row.created_at is None:
            await self._session.refresh(row)
        return MemoryMessage(
            id=row.id,
            role=row.role,
            content=row.content,
            created_at=row.created_at,
        )

    async def count_user_messages_since(self, user_id: int, since: datetime) -> int:
        stmt = select(func.count()).select_from(ConversationMessageORM).where(
            ConversationMessageORM.user_id == user_id,
            ConversationMessageORM.role == "user",
            ConversationMessageORM.created_at >= since,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_oldest_user_message_since(
        self, user_id: int, since: datetime
    ) -> datetime | None:
        stmt = select(func.min(ConversationMessageORM.created_at)).where(
            ConversationMessageORM.user_id == user_id,
            ConversationMessageORM.role == "user",
            ConversationMessageORM.created_at >= since,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent_messages(self, user_id: int, limit: int) -> list[MemoryMessage]:
        stmt = (
            select(
                ConversationMessageORM.id,
                ConversationMessageORM.role,
                ConversationMessageORM.content,
                ConversationMessageORM.created_at,
            )
            .where(ConversationMessageORM.user_id == user_id)
            .order_by(ConversationMessageORM.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            MemoryMessage(
                id=row.id,
                role=row.role,
                content=row.content,
                created_at=row.created_at,
            )
            for row in reversed(rows)
        ]

    async def search_messages(
        self, user_id: int, query: str, limit: int
    ) -> list[MemoryMessage]:
        stripped_query = query.strip()
        if not stripped_query:
            return []

        ts_query = func.plainto_tsquery("simple", stripped_query)
        rank = func.ts_rank_cd(ConversationMessageORM.content_tsv, ts_query)
        stmt = (
            select(
                ConversationMessageORM.id,
                ConversationMessageORM.role,
                ConversationMessageORM.content,
                ConversationMessageORM.created_at,
            )
            .where(
                ConversationMessageORM.user_id == user_id,
                ConversationMessageORM.content_tsv.op("@@")(ts_query),
            )
            .order_by(rank.desc(), ConversationMessageORM.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            MemoryMessage(
                id=row.id,
                role=row.role,
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_latest_summary(self, user_id: int) -> MemorySummary | None:
        stmt = (
            select(
                ConversationSummaryORM.summary,
                ConversationSummaryORM.max_message_id,
                ConversationSummaryORM.created_at,
            )
            .where(ConversationSummaryORM.user_id == user_id)
            .order_by(ConversationSummaryORM.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return MemorySummary(
            summary=row.summary,
            max_message_id=row.max_message_id,
            created_at=row.created_at,
        )

    async def get_messages_after_id(
        self, user_id: int, message_id: int, limit: int
    ) -> list[MemoryMessage]:
        stmt = (
            select(
                ConversationMessageORM.id,
                ConversationMessageORM.role,
                ConversationMessageORM.content,
                ConversationMessageORM.created_at,
            )
            .where(
                ConversationMessageORM.user_id == user_id,
                ConversationMessageORM.id > message_id,
            )
            .order_by(ConversationMessageORM.id.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            MemoryMessage(
                id=row.id,
                role=row.role,
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def save_summary(
        self, user_id: int, summary: str, max_message_id: int
    ) -> MemorySummary:
        row = ConversationSummaryORM(
            user_id=user_id,
            summary=summary,
            max_message_id=max_message_id,
        )
        self._session.add(row)
        await self._session.flush()
        if row.created_at is None:
            await self._session.refresh(row)
        return MemorySummary(
            summary=row.summary,
            max_message_id=row.max_message_id,
            created_at=row.created_at,
        )
