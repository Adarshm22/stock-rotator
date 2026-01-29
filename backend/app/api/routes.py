"""API routes for stock rotator."""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.csv_rotator import rotator
from app.services.gemini import gemini_service
from app.services.conditions import create_condition, get_all_conditions


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/row")
def get_row() -> dict:
    """Get current CSV row with metadata."""
    row_data = rotator.get_current()
    return {
        "row": row_data,
        "index": rotator.get_index(),
        "total": rotator.get_total(),
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Process natural language trading condition.
    
    Accepts user message, parses it with Gemini AI, creates condition,
    and returns structured response with timestamps.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get row and index atomically
    with rotator.lock:
        row = rotator.get_current()
        current_index = rotator.get_index()
    
    print(f"[CHAT] Calling Gemini API...")
    try:
        parsed = gemini_service.parse_condition(message, row)
        print(f"[CHAT] Gemini responded successfully")
    except Exception as e:
        print(f"[CHAT] Gemini error: {e}")
        raise
    
    # Create condition
    condition = create_condition(
        message=message,
        assistant_message=parsed["assistant_message"],
        spec=parsed["spec"],
        command_time=request.command_time,
        row=row,
        row_index=current_index,
    )

    return ChatResponse(
        id=condition["id"],
        status=condition["status"],
        message=condition["message"],
        command_time=condition["command_time"],
        parsed_time=condition["parsed_time"],
        last_checked_time=condition["last_checked_time"],
        triggered_time=condition["triggered_time"],
        assistant_message=condition["assistant_message"],
        spec=condition["spec"],
    )


@router.get("/conditions")
def get_conditions() -> list[dict]:
    """Get all trading conditions sorted by creation time (newest first)."""
    return get_all_conditions()
