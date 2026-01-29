"""CSV data rotation and management."""
from __future__ import annotations

import csv
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Callable

from app.config import config


class CsvRowRotator:
    """Manages CSV data loading, rotation, and state persistence."""
    
    def __init__(self, csv_path: Path | None = None) -> None:
        self.csv_path = self._resolve_path(csv_path)
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.index = 0
        self.lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[Dict[str, str], int], None]] = []
        
        self._load_csv()
        self._load_state()

    def _resolve_path(self, csv_path: Path | None) -> Path:
        """Resolve CSV file path from provided path or defaults."""
        if csv_path and csv_path.exists():
            return csv_path
        
        if config.CSV_PATH and config.CSV_PATH.exists():
            return config.CSV_PATH
            
        for candidate in config.DEFAULT_CSV_PATHS:
            if candidate.exists():
                return candidate
        
        raise FileNotFoundError(
            "CSV file not found. Set CSV_PATH env or include NIFTY_historical_data.csv"
        )

    def _load_csv(self) -> None:
        """Load CSV file into memory."""
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            self.headers = next(reader)
            self.rows = [row for row in reader if row]
        
        if not self.rows:
            raise ValueError("CSV file contains no data rows")

    def _load_state(self) -> None:
        """Load persisted state from disk."""
        if not config.STATE_PATH.exists():
            return
        
        try:
            state = json.loads(config.STATE_PATH.read_text(encoding="utf-8"))
            index = int(state.get("index", 0))
            if 0 <= index < len(self.rows):
                self.index = index
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    def _save_state(self) -> None:
        """Persist current state to disk."""
        try:
            state = {"index": self.index}
            config.STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except (OSError, IOError):
            pass

    def register_callback(self, callback: Callable[[Dict[str, str], int], None]) -> None:
        """Register a callback to be called on each row update."""
        self._callbacks.append(callback)

    def get_current(self) -> Dict[str, str]:
        """Get current row as dictionary."""
        with self.lock:
            row = self.rows[self.index]
            return dict(zip(self.headers, row))

    def get_index(self) -> int:
        """Get current row index."""
        with self.lock:
            return self.index

    def _rotate(self) -> None:
        """Advance to next row and save state."""
        with self.lock:
            self.index = (self.index + 1) % len(self.rows)
            self._save_state()
            
            # Notify callbacks
            row = self.get_current()
            index = self.index
        
        # Call callbacks outside lock to prevent deadlock
        for callback in self._callbacks:
            try:
                callback(row, index)
            except Exception:
                pass  # Don't let callback errors stop rotation

    def _run(self) -> None:
        """Background thread main loop."""
        while not self._stop_event.is_set():
            time.sleep(config.UPDATE_INTERVAL_SECONDS)
            if not self._stop_event.is_set():
                self._rotate()

    def start(self) -> None:
        """Start background rotation thread."""
        if self._thread is not None:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="CSVRotator")
        self._thread.start()

    def stop(self) -> None:
        """Stop background rotation thread."""
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
