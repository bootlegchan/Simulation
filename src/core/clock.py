from datetime import datetime, timedelta, timezone
from typing import Any, Dict

class SimulationClock:
    """Independent simulation clock tracking tick counts and virtual ISO time."""

    def __init__(self, start_time_iso: str = "2026-01-01T06:00:00Z", ticks_per_minute: int = 1):
        clean_iso = start_time_iso.replace("Z", "+00:00")
        self.start_time = datetime.fromisoformat(clean_iso).astimezone(timezone.utc)
        self.ticks_per_minute = ticks_per_minute
        self.current_tick = 0
        self.is_paused = True

    @property
    def current_virtual_time(self) -> datetime:
        minutes_elapsed = self.current_tick / float(self.ticks_per_minute)
        return self.start_time + timedelta(minutes=minutes_elapsed)

    @property
    def current_virtual_time_iso(self) -> str:
        return self.current_virtual_time.isoformat()

    def advance_tick(self, count: int = 1) -> int:
        if self.is_paused:
            from src.core.errors import LifecycleError
            raise LifecycleError("Cannot advance clock while simulation is paused.")
        self.current_tick += count
        return self.current_tick

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time_iso": self.start_time.isoformat(),
            "ticks_per_minute": self.ticks_per_minute,
            "current_tick": self.current_tick,
            "is_paused": self.is_paused,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationClock":
        clock = cls(
            start_time_iso=data["start_time_iso"],
            ticks_per_minute=data.get("ticks_per_minute", 1)
        )
        clock.current_tick = data.get("current_tick", 0)
        clock.is_paused = data.get("is_paused", True)
        return clock
