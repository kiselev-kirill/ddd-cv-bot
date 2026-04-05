from datetime import UTC, datetime, timedelta

from src.domain.memory.entities import (
    MemoryContext,
    MemoryMessage,
    MemoryQuota,
    MemorySummary,
)
from src.domain.memory.repository import AbstractMemoryRepository


class MemoryService:
    def __init__(
        self,
        repository: AbstractMemoryRepository,
        *,
        user_message_limit: int,
        window_minutes: int,
        recent_messages_limit: int,
        search_results_limit: int,
        summary_trigger_messages: int,
        summary_source_messages: int,
    ) -> None:
        self._repository = repository
        self._user_message_limit = user_message_limit
        self._window = timedelta(minutes=window_minutes)
        self._recent_messages_limit = recent_messages_limit
        self._search_results_limit = search_results_limit
        self._summary_trigger_messages = summary_trigger_messages
        self._summary_source_messages = summary_source_messages

    async def ensure_user(self, user_id: int, username: str | None) -> None:
        await self._repository.upsert_user(user_id=user_id, username=username)

    async def check_quota(self, user_id: int) -> MemoryQuota:
        now_utc = datetime.now(UTC)
        window_start = now_utc - self._window
        used = await self._repository.count_user_messages_since(
            user_id=user_id,
            since=window_start,
        )
        if used < self._user_message_limit:
            return MemoryQuota(
                allowed=True,
                used=used,
                limit=self._user_message_limit,
                blocked_until=None,
            )

        oldest = await self._repository.get_oldest_user_message_since(
            user_id=user_id,
            since=window_start,
        )
        blocked_until = oldest + self._window if oldest else None
        return MemoryQuota(
            allowed=False,
            used=used,
            limit=self._user_message_limit,
            blocked_until=blocked_until,
        )

    async def build_context(self, user_id: int, question: str) -> MemoryContext:
        latest_summary = await self._repository.get_latest_summary(user_id=user_id)
        recent = await self._repository.get_recent_messages(
            user_id=user_id,
            limit=self._recent_messages_limit,
        )
        relevant = await self._repository.search_messages(
            user_id=user_id,
            query=question,
            limit=self._search_results_limit,
        )

        recent_ids = {(msg.id, msg.role, msg.content, msg.created_at) for msg in recent}
        relevant_filtered = [
            msg
            for msg in relevant
            if (msg.id, msg.role, msg.content, msg.created_at) not in recent_ids
        ]

        return MemoryContext(
            latest_summary=latest_summary,
            recent_messages=recent,
            relevant_messages=relevant_filtered,
        )

    async def save_turn(
        self,
        *,
        user_id: int,
        user_text: str,
        assistant_reply: str,
    ) -> tuple[MemoryMessage, MemoryMessage]:
        user_message = await self._repository.add_message(
            user_id=user_id,
            role="user",
            content=user_text,
        )
        assistant_message = await self._repository.add_message(
            user_id=user_id,
            role="assistant",
            content=assistant_reply,
        )
        return user_message, assistant_message

    async def update_summary_if_needed(self, user_id: int) -> MemorySummary | None:
        latest_summary = await self._repository.get_latest_summary(user_id=user_id)
        last_summary_message_id = latest_summary.max_message_id if latest_summary else 0
        new_messages = await self._repository.get_messages_after_id(
            user_id=user_id,
            message_id=last_summary_message_id,
            limit=self._summary_source_messages,
        )
        if not new_messages:
            return None

        if len(new_messages) < self._summary_trigger_messages:
            return None

        summary_text = self._build_summary_text(
            previous_summary=latest_summary.summary if latest_summary else "",
            messages=new_messages,
        )
        max_message_id = max(message.id for message in new_messages)
        return await self._repository.save_summary(
            user_id=user_id,
            summary=summary_text,
            max_message_id=max_message_id,
        )

    @staticmethod
    def _build_summary_text(previous_summary: str, messages: list[MemoryMessage]) -> str:
        lines: list[str] = []
        if previous_summary:
            trimmed_previous = previous_summary.strip()[:900]
            lines.append(f"Summary so far: {trimmed_previous}")

        lines.append("Recent highlights:")
        for msg in messages[-20:]:
            role = "Recruiter" if msg.role == "user" else "Candidate"
            text = msg.content.strip().replace("\n", " ")
            lines.append(f"- {role}: {text[:160]}")

        return "\n".join(lines)[:2500]

    @staticmethod
    def format_context(context: MemoryContext) -> str:
        summary_block = ""
        if context.latest_summary:
            summary_text = context.latest_summary.summary.strip().replace("\n", " ")
            summary_block = f"Conversation summary:\n- {summary_text[:1500]}"

        def _format(messages: list[MemoryMessage], title: str) -> str:
            if not messages:
                return ""
            rows = [title]
            for msg in messages:
                safe_text = msg.content.strip().replace("\n", " ")
                trimmed = safe_text[:600]
                rows.append(f"- {msg.role}: {trimmed}")
            return "\n".join(rows)

        parts = [
            summary_block,
            _format(context.recent_messages, "Recent chat history:"),
            _format(context.relevant_messages, "Relevant older messages:"),
        ]
        return "\n\n".join(part for part in parts if part).strip()
