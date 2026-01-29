"""CSV row rotation service."""
import csv
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


class CsvRowRotator:
    """Manages CSV data rotation and state persistence."""
    
    def __init__(self, csv_path: Path | None) -> None:
        self.csv_path = self._resolve_path(csv_path)
        self.headers: list[str] = []
        self.rows: list[list[str]] = []
        self.index = 0
        self.lock = threading.RLock()
        self._load_csv()
        self._load_state()

    def _load_csv(self) -> None:
        """Load CSV file into memory."""
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            self.headers = next(reader)
            self.rows = [row for row in reader if row]
        if not self.rows:
            raise ValueError("CSV file contains no data rows")

    def _resolve_path(self, csv_path: Path | None) -> Path:
        """Resolve CSV file path from config or defaults."""
        if csv_path and csv_path.exists():
            return csv_path
        for candidate in settings.DEFAULT_DATA_PATHS:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "CSV file not found. Set CSV_PATH env or include NIFTY_historical_data.csv in backend/"
        )

    def _load_state(self) -> None:
        """Load saved state from disk."""
        state_path = Path(settings.STATE_PATH)
        if not state_path.exists():
            return
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            index = int(state.get("index", 0))
        except (ValueError, TypeError, json.JSONDecodeError):
            return
        with self.lock:
            self.index = index % len(self.rows)

    def _save_state(self) -> None:
        """Save current state to disk."""
        state_path = Path(settings.STATE_PATH)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"index": self.index}), encoding="utf-8"
        )

    def get_current(self) -> dict[str, str]:
        """Get current row as dictionary."""
        with self.lock:
            row = self.rows[self.index]
            return dict(zip(self.headers, row))

    def get_index(self) -> int:
        """Get current row index."""
        with self.lock:
            return self.index

    def get_total(self) -> int:
        """Get total number of rows."""
        return len(self.rows)

    def advance(self) -> None:
        """Advance to next row and evaluate conditions."""
        from app.services.conditions import evaluate_pending_conditions
        
        with self.lock:
            self.index = (self.index + 1) % len(self.rows)
            self._save_state()
            current_row = dict(zip(self.headers, self.rows[self.index]))
            current_index = self.index
        evaluate_pending_conditions(current_row, current_index)

    def start(self) -> None:
        """Start background rotation thread."""
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()

    def _run_loop(self) -> None:
        """Background loop for automatic row rotation."""
        while True:
            time.sleep(settings.UPDATE_INTERVAL_SECONDS)
            self.advance()


# Global rotator instance
rotator = CsvRowRotator(Path(settings.CSV_PATH) if settings.CSV_PATH else None)
