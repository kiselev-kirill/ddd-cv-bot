from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.memory.entities import MemoryMessage
from src.domain.memory.repository import AbstractMemoryRepository
from src.infrastructure.postgres.tables import BotUserORM, ConversationMessageORM


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
            MemoryMessage(role=row.role, content=row.content, created_at=row.created_at)
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
            MemoryMessage(role=row.role, content=row.content, created_at=row.created_at)
            for row in rows
        ]
