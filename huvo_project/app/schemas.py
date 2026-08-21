from typing import Literal

from pydantic import BaseModel, Field

Channel = Literal["chat", "voice"]
Configuration = Literal["2bhk", "3bhk"]


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    channel: Channel = "chat"


class ChatReply(BaseModel):
    reply: str
    ended: bool = False


class EndRequest(BaseModel):
    session_id: str = Field(min_length=1)


class Response(BaseModel):
    """Captured information from a single user message during conversation."""
    message: str
    intent: Literal["interest", "objection", "question", "booking", "callback", "opt_out", "unknown"] | None = "unknown"
    configuration: Literal["2bhk", "3bhk", "unknown"] | None = None
    budget: str | None = None
    interest_level: Literal["hot", "warm", "cold"] | None = None
    objections: list[str] = Field(default_factory=list)
    phone: str | None = None
    name: str | None = None
    notes: str | None = None


class Analytics(BaseModel):
    language: Literal["english", "hindi", "hinglish"] | None = None
    configuration: Literal["2bhk", "3bhk", "unknown"] | None = "unknown"
    budget: str | None = None
    interest_level: Literal["hot", "warm", "cold", "unknown"] | None = (
        "unknown"
    )
    site_visit_status: Literal[
        "booked", "failed", "not_requested", "unknown"
    ] | None = "unknown"
    follow_up_required: bool | None = None
    objections: list[str] = Field(default_factory=list)
    outcome: Literal[
        "booked",
        "callback",
        "opted_out",
        "escalated",
        "browsing",
        "unknown",
    ] | None = "unknown"
    opted_out: bool = False
    escalated: bool = False
    callback_time: str | None = None
    notes: str | None = None


class BookSiteVisitArgs(BaseModel):
    customer_name: str
    phone: str
    configuration: Configuration
    visit_date: str
    visit_time: str


class ScheduleCallbackArgs(BaseModel):
    customer_name: str
    phone: str
    when: str


class OptOutArgs(BaseModel):
    reason: str = "customer_request"


class EscalateArgs(BaseModel):
    reason: str
    phone: str | None = None


class ReopenSessionRequest(BaseModel):
    session_id: str = Field(min_length=1)


class UpdateAnalyticsRequest(BaseModel):
    session_id: str = Field(min_length=1)
    analytics: dict = Field(default_factory=dict)


class SessionDataResponse(BaseModel):
    session_id: str
    messages: list[dict]
    channel: Channel
    ended: bool
    responses: list[dict] | None = None
    analytics: dict | None = None


class EndConversationResponse(BaseModel):
    """Response when conversation ends - analytics hidden from user, saved internally."""
    message: str
    session_id: str
