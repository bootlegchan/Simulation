"""Simulation Clock and Virtual Time tracking."""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from src.core.errors import LifecycleError

class SimulationClock:
    """Discrete virtual simulation clock advancing in integer ticks."""

    def __init__(self, start_time_iso: str = "2026-01-01T06:00:00Z", ticks_per_minute: int = 1):
        self.start_time_iso = start_time_iso
        self.ticks_per_minute = max(1, ticks_per_minute)
        self.current_tick: int = 0
        self.is_paused: bool = True
        clean_iso = start_time_iso.replace("Z", "+00:00")
        self._start_dt = datetime.fromisoformat(clean_iso)

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def advance_tick(self, count: int = 1) -> int:
        if self.is_paused:
            raise LifecycleError("Cannot advance simulation clock while paused.")
        if count < 0:
            raise ValueError("Tick advancement count must be non-negative.")
        self.current_tick += count
        return self.current_tick

    @property
    def current_virtual_time(self) -> datetime:
        minutes_elapsed = self.current_tick / self.ticks_per_minute
        return self._start_dt + timedelta(minutes=minutes_elapsed)

    @property
    def current_virtual_time_iso(self) -> str:
        return self.current_virtual_time.isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time_iso": self.start_time_iso,
            "ticks_per_minute": self.ticks_per_minute,
            "current_tick": self.current_tick,
            "is_paused": self.is_paused,
            "current_virtual_time_iso": self.current_virtual_time_iso
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationClock":
        clock = cls(
            start_time_iso=data.get("start_time_iso", "2026-01-01T06:00:00Z"),
            ticks_per_minute=data.get("ticks_per_minute", 1)
        )
        clock.current_tick = data.get("current_tick", 0)
        clock.is_paused = data.get("is_paused", True)
        return clock
