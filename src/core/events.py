"""In-memory domain event bus and pub/sub distribution."""
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

class EventBus:
    """Publish-subscribe domain event dispatcher."""

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
        should_store = True
        max_hist = 2000
        if self.log_manager is not None:
            try:
                from src.core.logging_config import LogChannel
                should_store = self.log_manager.is_channel_enabled(LogChannel.DOMAIN_EVENTS)
                max_hist = getattr(self.log_manager, "max_event_history", 2000)
            except Exception:
                should_store = True

        if should_store:
            self.history.append(event)
            if len(self.history) > max_hist:
                self.history = self.history[-max_hist:]

        for cb in self._subscribers.get(event.event_type, []):
            cb(event)

        for cb in self._subscribers.get("*", []):
            cb(event)

    def clear(self) -> None:
        self.history.clear()
