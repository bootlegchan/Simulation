from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import uuid

@dataclass
class DomainEvent:
    event_type: str
    tick: int
    source_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "tick": self.tick,
            "source_id": self.source_id,
            "payload": self.payload,
            "timestamp_iso": self.timestamp_iso,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            tick=data["tick"],
            source_id=data["source_id"],
            payload=data["payload"],
            timestamp_iso=data["timestamp_iso"],
        )

EventHandler = Callable[[DomainEvent], None]

class EventBus:
    """Append-only event log with subscriber dispatch and sliding compaction."""

    def __init__(self):
        self._history: List[DomainEvent] = []
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._total_published_count: int = 0

    @property
    def history(self) -> List[DomainEvent]:
        return list(self._history)

    @property
    def events(self) -> List[DomainEvent]:
        return list(self._history)

    @property
    def total_events_published(self) -> int:
        return self._total_published_count

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        self._history.append(event)
        self._total_published_count += 1
        for h in self._subscribers.get(event.event_type, []):
            h(event)
        for h in self._subscribers.get("*", []):
            h(event)

    def compact_history(self, keep_last_n: int = 1000) -> int:
        """Prunes historical events while retaining total count for long simulation runs."""
        if len(self._history) > keep_last_n:
            pruned_count = len(self._history) - keep_last_n
            self._history = self._history[-keep_last_n:]
            return pruned_count
        return 0

    def query(
        self,
        event_type: Optional[str] = None,
        source_id: Optional[str] = None,
        min_tick: Optional[int] = None,
        max_tick: Optional[int] = None,
    ) -> List[DomainEvent]:
        res = self._history
        if event_type:
            res = [e for e in res if e.event_type == event_type]
        if source_id:
            res = [e for e in res if e.source_id == source_id]
        if min_tick is not None:
            res = [e for e in res if e.tick >= min_tick]
        if max_tick is not None:
            res = [e for e in res if e.tick <= max_tick]
        return res

    def clear(self) -> None:
        self._history.clear()
        self._total_published_count = 0

    def to_dict(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._history]

    def load_history(self, events_data: List[Dict[str, Any]]) -> None:
        self._history = [DomainEvent.from_dict(ed) for ed in events_data]
        self._total_published_count = len(self._history)
