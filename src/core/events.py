"""In-memory domain event bus, pub/sub distribution, and browser-facing event streaming."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import time

@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    tick: int
    source_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "tick": self.tick,
            "source_id": self.source_id,
            "payload": dict(self.payload),
            "timestamp": round(self.timestamp, 4)
        }

class EventBus:
    """Publish-subscribe domain event dispatcher with live event streaming and queryable audit trails."""

    def __init__(self, log_manager: Optional[Any] = None):
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
        self.history: List[DomainEvent] = []
        self.log_manager = log_manager

    def subscribe(self, event_type: str, callback: Callable[[DomainEvent], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[DomainEvent], None]) -> None:
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: DomainEvent) -> None:
        max_hist = 5000
        if self.log_manager is not None:
            max_hist = getattr(self.log_manager, "max_event_history", 5000)

        self.history.append(event)
        if len(self.history) > max_hist:
            self.history = self.history[-max_hist:]

        for cb in self._subscribers.get(event.event_type, []):
            cb(event)

        for cb in self._subscribers.get("*", []):
            cb(event)

    def get_stream(self, since_timestamp: float = 0.0, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns new chronological events emitted strictly after since_timestamp for live UI polling/SSE."""
        matching = [
            e.to_dict() for e in self.history
            if e.timestamp > since_timestamp
        ]
        return matching[:limit]

    def query_events(
        self,
        event_type: Optional[str] = None,
        source_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        min_tick: int = 0,
        max_tick: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Filter historical domain events by event type, source service, involved entity, and tick range."""
        results: List[Dict[str, Any]] = []
        for e in reversed(self.history):
            if min_tick > 0 and e.tick < min_tick:
                continue
            if max_tick is not None and e.tick > max_tick:
                continue
            if event_type and e.event_type != event_type:
                continue
            if source_id and e.source_id != source_id:
                continue
            if entity_id:
                # Check source_id or any entity reference in payload
                matches_entity = (
                    e.source_id == entity_id
                    or any(v == entity_id for v in e.payload.values() if isinstance(v, str))
                )
                if not matches_entity:
                    continue

            results.append(e.to_dict())
            if len(results) >= limit:
                break

        results.reverse()
        return results

    def get_entity_timeline(self, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the chronological domain event audit trail for an individual citizen or building."""
        return self.query_events(entity_id=entity_id, limit=limit)

    def clear(self) -> None:
        self.history.clear()
