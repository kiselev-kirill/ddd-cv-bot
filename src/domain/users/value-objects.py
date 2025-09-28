from dataclasses import dataclass
from datetime import datetime

from ..enums import ButtonType


@dataclass(frozen=True, kw_only=True)
class ButtonClickEvent:
    user_id: int
    button: ButtonType
    clicked_at: datetime


@dataclass(frozen=True, kw_only=True)
class ReplyEvent:
    user_id: int
    reply_text: str
    source: str
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class SessionEvent:
    user_id: int
    started_at: datetime
    ended_at: datetime