from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1)


class RecommendRequest(BaseModel):
    question: Optional[str] = None
    messages: list[ChatMessage] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=3, ge=1, le=5)


class NextStep(str, Enum):
    ask = "ask"
    recommend = "recommend"


class ElicitationQuestion(BaseModel):
    id: str
    question: str
    choices: Optional[list[str]] = None


class CarRecommendation(BaseModel):
    model: str
    match_score: float = Field(ge=0, le=1)
    short_reason: str
    pros: list[str]
    cons: list[str]
    price_vnd: Optional[int] = None
    seats: Optional[int] = None


class RecommendResponse(BaseModel):
    next_step: NextStep
    assistant_message: str
    questions: list[ElicitationQuestion] = Field(default_factory=list)
    recommendations: list[CarRecommendation] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    handoff_to_human: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)


class FeedbackEvent(BaseModel):
    event_type: Literal["user_choice", "purchase", "thumbs"]
    session_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class UserProfile:
    budget_vnd: Optional[int]
    seats: Optional[int]
