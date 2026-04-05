from dataclasses import dataclass
from datetime import datetime


MessageRole = str


@dataclass(frozen=True, slots=True)
class MemoryMessage:
    id: int
    role: MessageRole
    content: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class MemoryQuota:
    allowed: bool
    used: int
    limit: int
    blocked_until: datetime | None


@dataclass(frozen=True, slots=True)
class MemorySummary:
    summary: str
    max_message_id: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class MemoryContext:
    latest_summary: MemorySummary | None
    recent_messages: list[MemoryMessage]
    relevant_messages: list[MemoryMessage]
