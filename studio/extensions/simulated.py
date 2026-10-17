"""A simulated external system of record, with failure injection.

External business systems stay authoritative (FR36): the platform never owns
the calendar, it reads and writes one through an adapter. Until a business
connects a real system, this stands in for it — with the properties that make
"verified" mean something:

* an effect honours the Core-issued idempotency key, so a retry never books
  twice and a different key is never suppressed (AD-10, FR55);
* success is confirmed by a separate read-back, not by the write's own return
  value (FR51) — so ``drop_writes`` (the write says yes and nothing lands) is
  caught as *unverified*;
* reads, writes and read-backs can each be made to fail or hang, so every
  failure path of the Core can be exercised (FR96).

Generic over businesses: a slot is identified by whichever arguments name a
date and a time, and a write stores the whole payload under its key.
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

from studio.core.ports import AdapterResult


def _field(arguments: dict[str, Any], suffix: str) -> Optional[str]:
    for name, value in arguments.items():
        if name == suffix or name.endswith("_" + suffix):
            return str(value)
    return None


@dataclass
class SimulatedCalendar:
    """Open times per date; bookings per tenant keyed by idempotency key."""

    name: str = "calendar"
    open_times: dict[str, tuple[str, ...]] = field(default_factory=dict)
    default_times: tuple[str, ...] = ("09:00", "11:00", "14:00", "16:00")
    tenant_times: dict[str, tuple[str, ...]] = field(default_factory=dict)
    fail_reads: bool = False
    fail_writes: bool = False
    drop_writes: bool = False
    hang_writes_s: float = 0.0
    fail_read_backs: bool = False

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self.bookings: dict[tuple[str, str], dict[str, Any]] = {}
        self.executions: Counter[tuple[str, str]] = Counter()

    def _taken(self, tenant: str, day: str) -> set[str]:
        return {_field(b, "time") for (t, _), b in self.bookings.items() if t == tenant and _field(b, "date") == day}

    def read(self, tenant: str, operation: str, arguments: dict[str, Any]) -> AdapterResult:
        if self.fail_reads:
            return AdapterResult(ok=False, error="the calendar is unavailable")
        if operation != "availability":
            return AdapterResult(ok=False, error=f"unknown read {operation}")
        day = _field(arguments, "date")
        with self._lock:
            times = self.open_times.get(day, self.tenant_times.get(tenant, self.default_times))
            free = [t for t in times if t not in self._taken(tenant, day)]
        return AdapterResult(ok=True, data=(("date", day), ("open_times", ", ".join(free) or "none")))

    def effect(self, tenant: str, operation: str, arguments: dict[str, Any], idempotency_key: str) -> AdapterResult:
        if self.hang_writes_s:
            time.sleep(self.hang_writes_s)
        if self.fail_writes:
            return AdapterResult(ok=False, error="the calendar rejected the write")
        key = (tenant, idempotency_key)
        with self._lock:
            self.executions[key] += 1
            if key in self.bookings:
                return AdapterResult(ok=True, reference=self.bookings[key]["reference"])
            day, at = _field(arguments, "date"), _field(arguments, "time")
            if at and at in self._taken(tenant, day):
                return AdapterResult(ok=False, error=f"{day} {at} is no longer free")
            reference = f"BK-{len(self.bookings) + 1:04d}"
            if not self.drop_writes:
                self.bookings[key] = {**arguments, "reference": reference}
        return AdapterResult(ok=True, reference=reference)

    def read_back(self, tenant: str, operation: str, arguments: dict[str, Any], idempotency_key: str,
                  reference: Optional[str]) -> AdapterResult:
        if self.fail_read_backs:
            raise ConnectionError("the calendar did not answer the read-back")
        with self._lock:
            stored = self.bookings.get((tenant, idempotency_key))
        if stored is None:
            return AdapterResult(ok=False, error="no such booking")
        matches = all(str(stored.get(k)) == str(v) for k, v in arguments.items())
        return AdapterResult(ok=matches, reference=stored["reference"],
                             error=None if matches else "the stored booking differs from the request")
