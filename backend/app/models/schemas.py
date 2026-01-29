"""Pydantic models for request/response validation."""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    command_time: str | None = None


class ConditionSpec(BaseModel):
    """Specification for a trading condition."""
    field: str
    operator: str
    value: str
    value_type: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    id: str
    status: str
    message: str
    command_time: str
    parsed_time: str
    last_checked_time: str
    triggered_time: str | None
    assistant_message: str
    spec: dict[str, str]
