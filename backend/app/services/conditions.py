"""Trading conditions management service."""
import threading
from datetime import datetime, timezone
from uuid import uuid4


# Global conditions storage
conditions_lock = threading.Lock()
conditions: dict[str, dict[str, object]] = {}


def _now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _parse_number(value: str) -> float | None:
    """Parse a string to a number, handling commas."""
    try:
        cleaned = value.replace(",", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def evaluate_condition(row: dict[str, str], spec: dict[str, str]) -> bool:
    """
    Evaluate if a row matches the condition specification.
    
    Args:
        row: CSV row data as dictionary
        spec: Condition spec with field, operator, value, value_type
        
    Returns:
        True if condition is met, False otherwise
    """
    field = spec.get("field", "")
    operator = spec.get("operator", "")
    value = spec.get("value", "")
    value_type = spec.get("value_type", "string")

    if not field or field not in row:
        return False

    row_value = row[field]
    if value_type == "number":
        row_number = _parse_number(row_value)
        target_number = _parse_number(value)
        if row_number is None or target_number is None:
            return False
        left = row_number
        right = target_number
    else:
        left = str(row_value)
        right = str(value)

    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == "contains":
        return right.lower() in left.lower()
    if operator == "starts_with":
        return left.lower().startswith(right.lower())
    if operator == "ends_with":
        return left.lower().endswith(right.lower())
    return False


def evaluate_pending_conditions(row: dict[str, str], index: int) -> None:
    """
    Evaluate all pending conditions against the current row.
    
    Args:
        row: Current CSV row data
        index: Current row index
    """
    now = _now_iso()
    with conditions_lock:
        for condition in conditions.values():
            if condition["status"] != "pending":
                continue
            condition["last_checked_time"] = now
            if evaluate_condition(row, condition["spec"]):
                condition["status"] = "triggered"
                condition["triggered_time"] = now
                condition["matched_row_index"] = index
                condition["matched_row"] = row


def create_condition(
    message: str,
    assistant_message: str,
    spec: dict[str, str],
    command_time: str,
    row: dict[str, str],
    row_index: int,
) -> dict[str, object]:
    """
    Create a new trading condition.
    
    Args:
        message: User's original message
        assistant_message: AI's response message
        spec: Condition specification
        command_time: When user issued the command
        row: Current CSV row for immediate evaluation
        row_index: Current row index
        
    Returns:
        Created condition dictionary
    """
    now = _now_iso()
    condition_id = str(uuid4())
    
    status = "pending"
    triggered_time = None
    matched_row = None
    matched_row_index = None

    if evaluate_condition(row, spec):
        status = "triggered"
        triggered_time = now
        matched_row = row
        matched_row_index = row_index

    condition = {
        "id": condition_id,
        "message": message,
        "assistant_message": assistant_message,
        "spec": spec,
        "status": status,
        "command_time": command_time or now,
        "parsed_time": now,
        "last_checked_time": now,
        "triggered_time": triggered_time,
        "matched_row_index": matched_row_index,
        "matched_row": matched_row,
    }

    with conditions_lock:
        conditions[condition_id] = condition

    return condition


def get_all_conditions() -> list[dict[str, object]]:
    """Get all conditions sorted by parsed time (newest first)."""
    with conditions_lock:
        return sorted(
            conditions.values(),
            key=lambda c: c.get("parsed_time", ""),
            reverse=True,
        )
