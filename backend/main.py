from __future__ import annotations

import csv
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DATA_PATH = Path(__file__).resolve().parents[1] / "NIFTY_historical_data.csv"
UPDATE_INTERVAL_SECONDS = 60


class CsvRowRotator:
    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.index = 0
        self.lock = threading.Lock()
        self._load_csv()

    def _load_csv(self) -> None:
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            self.headers = next(reader)
            self.rows = [row for row in reader if row]
        if not self.rows:
            raise ValueError("CSV file contains no data rows")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
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
