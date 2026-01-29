"""Trading condition management and evaluation."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4


def _now_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _parse_number(value: str) -> float | None:
    """Parse string to number, handling comma separators."""
    try:
        cleaned = value.replace(",", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


class ConditionService:
    """Service for managing and evaluating trading conditions."""
    
    def __init__(self) -> None:
        self._conditions: Dict[str, Dict[str, object]] = {}
        self._lock = threading.Lock()
    
    def create_condition(
        self,
        message: str,
        command_time: str,
        parsed_data: Dict[str, object],
        current_row: Dict[str, str],
        current_index: int
    ) -> Dict[str, object]:
        """
        Create a new trading condition.
        
        Args:
            message: Original user message
            command_time: When command was issued
            parsed_data: Parsed condition from AI
            current_row: Current CSV row
            current_index: Current row index
            
        Returns:
            Complete condition dictionary
        """
        condition_id = str(uuid4())
        now = _now_iso()
        spec = parsed_data["spec"]
        
        # Check if condition is already met
        status = "pending"
        triggered_time = None
        matched_row = None
        matched_row_index = None
        
        if self.evaluate_condition(current_row, spec):
            status = "triggered"
            triggered_time = now
            matched_row = current_row
            matched_row_index = current_index
        
        condition = {
            "id": condition_id,
            "message": message,
            "assistant_message": parsed_data["assistant_message"],
            "spec": spec,
            "status": status,
            "command_time": command_time,
            "parsed_time": now,
            "last_checked_time": now,
            "triggered_time": triggered_time,
            "matched_row_index": matched_row_index,
            "matched_row": matched_row,
        }
        
        with self._lock:
            self._conditions[condition_id] = condition
        
        return condition
    
    def get_all_conditions(self) -> List[Dict[str, object]]:
        """Get all conditions sorted by parsed time descending."""
        with self._lock:
            conditions = list(self._conditions.values())
        
        return sorted(
            conditions,
            key=lambda c: c.get("parsed_time", ""),
            reverse=True
        )
    
    def evaluate_pending_conditions(
        self,
        row: Dict[str, str],
        index: int
    ) -> None:
        """
        Evaluate all pending conditions against current row.
        Called automatically on row rotation.
        """
        now = _now_iso()
        
        with self._lock:
            for condition in self._conditions.values():
                if condition["status"] != "pending":
                    continue
                
                condition["last_checked_time"] = now
                
                if self.evaluate_condition(row, condition["spec"]):
                    condition["status"] = "triggered"
                    condition["triggered_time"] = now
                    condition["matched_row_index"] = index
                    condition["matched_row"] = row
    
    @staticmethod
    def evaluate_condition(
        row: Dict[str, str],
        spec: Dict[str, str]
    ) -> bool:
        """
        Evaluate a single condition against a row.
        
        Args:
            row: CSV row data
            spec: Condition specification
            
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
        
        # Numeric comparison
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
        
        # Apply operator
        if operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        elif operator == ">":
            return left > right
        elif operator == ">=":
            return left >= right
        elif operator == "<":
            return left < right
        elif operator == "<=":
            return left <= right
        elif operator == "contains":
            return right.lower() in left.lower()
        elif operator == "starts_with":
            return left.lower().startswith(right.lower())
        elif operator == "ends_with":
            return left.lower().endswith(right.lower())
        
        return False


# Singleton instance
condition_service = ConditionService()
