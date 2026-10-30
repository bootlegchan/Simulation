import hashlib
import json
from typing import Any, Dict, List, Optional
from src.core.events import DomainEvent

class EventStore:
    """Immutable event sourcing store supporting tick-indexed querying and deterministic state replay."""

    def __init__(self):
        self.events: List[DomainEvent] = []
        self.tick_index: Dict[int, List[int]] = {}

    def append(self, event: DomainEvent) -> str:
        idx = len(self.events)
        self.events.append(event)
        
        if event.tick not in self.tick_index:
            self.tick_index[event.tick] = []
        self.tick_index[event.tick].append(idx)

        # Calculate state checksum hash
        event_bytes = json.dumps(event.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(event_bytes).hexdigest()[:12]

    def get_events_for_tick(self, tick: int) -> List[DomainEvent]:
        indices = self.tick_index.get(tick, [])
        return [self.events[i] for i in indices]

    def get_events_between(self, start_tick: int, end_tick: int) -> List[DomainEvent]:
        results = []
        for t in range(start_tick, end_tick + 1):
            results.extend(self.get_events_for_tick(t))
        return results

    def replay_events(self, start_tick: int, end_tick: int, state_handler_func) -> None:
        """Replay events within a tick window through a target state handler."""
        for event in self.get_events_between(start_tick, end_tick):
            state_handler_func(event)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.events]

    def load_from_dict(self, data: List[Dict[str, Any]]) -> None:
        self.events.clear()
        self.tick_index.clear()
        for e_dict in data:
            evt = DomainEvent.from_dict(e_dict)
            self.append(evt)
