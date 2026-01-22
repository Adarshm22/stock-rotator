from __future__ import annotations

import csv
import json
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DEFAULT_DATA_PATHS = [
    Path(__file__).resolve().parent / "NIFTY_historical_data.csv",
    Path(__file__).resolve().parents[1] / "NIFTY_historical_data.csv",
]
DATA_PATH = Path(os.getenv("CSV_PATH", "")).expanduser() if os.getenv("CSV_PATH") else None
UPDATE_INTERVAL_SECONDS = 60
DEFAULT_STATE_PATH = Path(os.getenv("STATE_PATH", "backend_state.json")).expanduser()


class CsvRowRotator:
    def __init__(self, csv_path: Path | None) -> None:
        self.csv_path = self._resolve_path(csv_path)
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.index = 0
        self.lock = threading.Lock()
        self._load_csv()
        self._load_state()

    def _load_csv(self) -> None:
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            self.headers = next(reader)
            self.rows = [row for row in reader if row]
        if not self.rows:
            raise ValueError("CSV file contains no data rows")

    def _resolve_path(self, csv_path: Path | None) -> Path:
        if csv_path and csv_path.exists():
            return csv_path
        for candidate in DEFAULT_DATA_PATHS:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "CSV file not found. Set CSV_PATH env or include NIFTY_historical_data.csv in backend/"
        )

    def _load_state(self) -> None:
        if not DEFAULT_STATE_PATH.exists():
            return
        try:
            state = json.loads(DEFAULT_STATE_PATH.read_text(encoding="utf-8"))
            index = int(state.get("index", 0))
        except (ValueError, TypeError, json.JSONDecodeError):
            return
        with self.lock:
            self.index = index % len(self.rows)

    def _save_state(self) -> None:
        DEFAULT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_STATE_PATH.write_text(
            json.dumps({"index": self.index}), encoding="utf-8"
        )

    def get_current(self) -> Dict[str, str]:
        with self.lock:
            row = self.rows[self.index]
            return dict(zip(self.headers, row))

    def get_index(self) -> int:
        with self.lock:
            return self.index

    def get_total(self) -> int:
        return len(self.rows)

    def advance(self) -> None:
        with self.lock:
            self.index = (self.index + 1) % len(self.rows)
            self._save_state()

    def start(self) -> None:
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()

    def _run_loop(self) -> None:
        while True:
            time.sleep(UPDATE_INTERVAL_SECONDS)
            self.advance()


rotator = CsvRowRotator(DATA_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    rotator.start()
    yield


app = FastAPI(lifespan=lifespan)

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:3000"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/row")
def get_row() -> Dict[str, object]:
    return {
        "index": rotator.get_index(),
        "total": rotator.get_total(),
        "row": rotator.get_current(),
    }
