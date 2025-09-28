from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    first_messaged_at: datetime
    _events: list = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class UserMessage:
    id: int
    user: User
    message: str
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class GeneratedReply:
    id: int
    user: User
    reply: str
    created_at: datetime


