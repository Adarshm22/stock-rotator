"""Data models and schemas."""
from __future__ import annotations

from typing import Dict
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User's natural language command")
    command_time: str | None = Field(None, description="ISO timestamp when command was issued")


class ConditionSpec(BaseModel):
    """Specification for a trading condition."""
    field: str = Field(..., description="CSV field name to evaluate")
    operator: str = Field(..., description="Comparison operator")
    value: str = Field(..., description="Value to compare against")
    value_type: str = Field(default="string", description="Type of value: number or string")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    id: str = Field(..., description="Unique condition identifier")
    status: str = Field(..., description="Condition status: pending or triggered")
    message: str = Field(..., description="Original user message")
    command_time: str = Field(..., description="When command was received")
    parsed_time: str = Field(..., description="When condition was parsed")
    last_checked_time: str = Field(..., description="Last evaluation time")
    triggered_time: str | None = Field(None, description="When condition was triggered")
    assistant_message: str = Field(..., description="AI assistant's response message")
    spec: Dict[str, str] = Field(..., description="Parsed condition specification")


class ConditionResponse(BaseModel):
    """Response model for a single condition."""
    id: str
    message: str
    assistant_message: str
    spec: Dict[str, str]
    status: str
    command_time: str
    parsed_time: str
    last_checked_time: str
    triggered_time: str | None
    matched_row_index: int | None = None
    matched_row: Dict[str, str] | None = None
