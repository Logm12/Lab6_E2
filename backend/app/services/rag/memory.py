from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class MemoryMessage:
    role: str
    content: str
    timestamp: str
    metadata: dict[str, Any]
    message_id: int


class EnhancedConversationMemory:
    def __init__(self, max_messages: int = 10) -> None:
        self._messages: list[MemoryMessage] = []
        self._max_messages = int(max_messages)

    def add_message(self, *, role: str, content: str, metadata: Optional[dict[str, Any]] = None) -> None:
        msg = MemoryMessage(
            role=str(role),
            content=str(content),
            timestamp=datetime.now().isoformat(),
            metadata=dict(metadata or {}),
            message_id=len(self._messages),
        )
        self._messages.append(msg)
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages :]

    def get_context(self, *, max_turns: int = 10) -> str:
        if not self._messages:
            return ""
        recent = self._messages[-int(max_turns) : -1]
        parts: list[str] = []
        for msg in recent:
            role_label = "User" if msg.role == "user" else "Assistant"
            content = msg.content
            sql = msg.metadata.get("sql")
            if msg.role == "assistant" and isinstance(sql, str) and sql.strip():
                parts.append(f"{role_label}: {content}\nSQL: {sql}")
            else:
                parts.append(f"{role_label}: {content}")
        return "\n\n".join(parts)

    def clear(self) -> None:
        self._messages = []

    def get_summary(self) -> str:
        if not self._messages:
            return "No conversation history"
        summary_lines: list[str] = []
        for msg in self._messages[-10:]:
            role_label = "User" if msg.role == "user" else "Assistant"
            preview = msg.content[:100]
            summary_lines.append(f"{role_label}: {preview}...")
        return "\n".join(summary_lines)
