"""API route handlers."""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse, ConditionResponse
from app.csv_rotator import CsvRowRotator
from app.gemini_service import gemini_service
from app.condition_service import condition_service
from datetime import datetime, timezone


router = APIRouter()


def _now_iso() -> str:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/row")
def get_current_row(rotator: CsvRowRotator) -> Dict[str, str | int]:
    """Get current CSV row with index."""
    with rotator.lock:
        row = rotator.get_current()
        index = rotator.get_index()
    
    return {
        **row,
        "index": index,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    rotator: CsvRowRotator
) -> ChatResponse:
    """
    Process natural language trading command.
    
    Args:
        request: Chat request with message and optional command_time
        rotator: CSV rotator instance (injected dependency)
        
    Returns:
        ChatResponse with parsed condition and status
    """
    # Get current row and index atomically
    with rotator.lock:
        current_row = rotator.get_current()
        current_index = rotator.get_index()
    
    # Parse condition with Gemini AI
    parsed_data = gemini_service.parse_trading_condition(
        request.message,
        current_row
    )
    
    # Create condition
    command_time = request.command_time or _now_iso()
    condition = condition_service.create_condition(
        message=request.message,
        command_time=command_time,
        parsed_data=parsed_data,
        current_row=current_row,
        current_index=current_index
    )
    
    return ChatResponse(
        id=condition["id"],
        status=condition["status"],
        message=condition["message"],
        command_time=condition["command_time"],
        parsed_time=condition["parsed_time"],
        last_checked_time=condition["last_checked_time"],
        triggered_time=condition.get("triggered_time"),
        assistant_message=condition["assistant_message"],
        spec=condition["spec"],
    )


@router.get("/conditions", response_model=List[ConditionResponse])
def get_conditions() -> List[ConditionResponse]:
    """Get all trading conditions sorted by creation time."""
    conditions = condition_service.get_all_conditions()
    
    return [
        ConditionResponse(
            id=c["id"],
            message=c["message"],
            assistant_message=c["assistant_message"],
            spec=c["spec"],
            status=c["status"],
            command_time=c["command_time"],
            parsed_time=c["parsed_time"],
            last_checked_time=c["last_checked_time"],
            triggered_time=c.get("triggered_time"),
            matched_row_index=c.get("matched_row_index"),
            matched_row=c.get("matched_row"),
        )
        for c in conditions
    ]
