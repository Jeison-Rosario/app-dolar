"""Shared, bounded cache for reference rates; no notification side effects."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import math
import re
from types import MappingProxyType
from typing import Mapping
import threading
import time
import requests

URL = "https://open.er-api.com/v6/latest/USD"

class RateError(Exception):
    pass

@dataclass(frozen=True)
class Snapshot:
    rates: Mapping[str, float]
    updated: datetime
    fetched: datetime
    stale: bool = False

def fetch_rate():
    try:
        response = requests.get(URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get("result") != "success" or data.get("base_code") != "USD":
            raise ValueError("Invalid response")
        raw_rates = data["rates"]
        if not isinstance(raw_rates, dict) or not raw_rates:
            raise ValueError("Invalid rates")
        rates = {}
        for code, raw in raw_rates.items():
            if not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code):
                raise ValueError("Invalid currency")
            if isinstance(raw, bool):
                raise ValueError("Invalid rate")
            rate = float(raw)
            if not math.isfinite(rate) or rate <= 0:
                raise ValueError("Invalid rate")
            rates[code] = rate
        if rates.get("USD") != 1:
            raise ValueError("Invalid base rate")
        updated = datetime.fromtimestamp(data["time_last_update_unix"], timezone.utc)
        return Snapshot(MappingProxyType(rates), updated, datetime.now(timezone.utc))
    except (requests.RequestException, ValueError, TypeError, KeyError, OverflowError, OSError) as exc:
        raise RateError("No se pudo obtener una cotización válida del proveedor.") from exc

def cross_rate(snapshot, source, target):
    """Units of target per unit of source, using the same USD snapshot."""
    try:
        return snapshot.rates[target] / snapshot.rates[source]
    except KeyError as exc:
        raise ValueError("Moneda no disponible en la cotización actual.") from exc

def convert(snapshot, amount, source, target):
    if isinstance(amount, bool) or not math.isfinite(amount) or amount < 0:
        raise ValueError("El importe debe ser un número finito no negativo.")
    return amount * cross_rate(snapshot, source, target)

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
