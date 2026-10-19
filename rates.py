"""Shared, bounded cache for reference rates; no notification side effects."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import math
import threading
import time
import requests

URL = "https://open.er-api.com/v6/latest/USD"

class RateError(Exception):
    pass

@dataclass(frozen=True)
class Snapshot:
    rate: float
    updated: datetime
    fetched: datetime
    stale: bool = False

def fetch_rate():
    try:
        response = requests.get(URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success" or data.get("base_code") != "USD":
            raise ValueError("Invalid response")
        raw = data["conversion_rates"]["DOP"]
        if isinstance(raw, bool):
            raise ValueError("Invalid rate")
        rate = float(raw)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("Invalid rate")
        updated = datetime.fromtimestamp(data["time_last_update_unix"], timezone.utc)
        return Snapshot(rate, updated, datetime.now(timezone.utc))
    except (requests.RequestException, ValueError, TypeError, KeyError, OverflowError, OSError) as exc:
        raise RateError("No se pudo obtener una cotización válida del proveedor.") from exc

class RateCache:
    def __init__(self, fetcher=fetch_rate, clock=time.monotonic):
        self.fetcher, self.clock = fetcher, clock
        self.snapshot = None
        self.next_attempt = 0
        self.failed = False
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            now = self.clock()
            if now >= self.next_attempt:
                try:
                    self.snapshot = self.fetcher()
                    self.failed = False
                    self.next_attempt = now + 3600
                except RateError:
                    self.failed = True
                    self.next_attempt = now + 60
            if self.snapshot is None:
                raise RateError("Proveedor no disponible. Vuelve a intentarlo en un minuto.")
            return replace(self.snapshot, stale=self.failed)
