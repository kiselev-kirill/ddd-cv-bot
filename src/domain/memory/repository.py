from abc import ABC, abstractmethod
from datetime import datetime

from .entities import MemoryMessage, MemorySummary


class AbstractMemoryRepository(ABC):
    @abstractmethod
    async def upsert_user(self, user_id: int, username: str | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, user_id: int, role: str, content: str) -> MemoryMessage:
        raise NotImplementedError

    @abstractmethod
    async def count_user_messages_since(self, user_id: int, since: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_oldest_user_message_since(
        self, user_id: int, since: datetime
    ) -> datetime | None:
        raise NotImplementedError

    @abstractmethod
    async def get_recent_messages(self, user_id: int, limit: int) -> list[MemoryMessage]:
        raise NotImplementedError

    @abstractmethod
    async def search_messages(
        self, user_id: int, query: str, limit: int
    ) -> list[MemoryMessage]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_summary(self, user_id: int) -> MemorySummary | None:
        raise NotImplementedError

    @abstractmethod
    async def get_messages_after_id(
        self, user_id: int, message_id: int, limit: int
    ) -> list[MemoryMessage]:
        raise NotImplementedError

    @abstractmethod
    async def save_summary(
        self, user_id: int, summary: str, max_message_id: int
    ) -> MemorySummary:
        raise NotImplementedError
