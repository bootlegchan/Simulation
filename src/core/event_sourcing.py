"""Event store for audit trails and temporal replays."""
from typing import Dict, List, Optional
from src.core.events import DomainEvent

class EventStore:
    """Sequential append-only log of domain events."""

    def __init__(self):
        self._events: List[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    def get_events_for_tick(self, tick: int) -> List[DomainEvent]:
        return [e for e in self._events if e.tick == tick]

    def get_events_by_type(self, event_type: str) -> List[DomainEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def get_events_by_source(self, source_id: str) -> List[DomainEvent]:
        return [e for e in self._events if e.source_id == source_id]

    @property
    def all_events(self) -> List[DomainEvent]:
        return list(self._events)
