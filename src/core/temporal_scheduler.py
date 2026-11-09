"""
Hierarchical Asynchronous Event-Scheduled Time (HAEST) Kernel.
Manages continuous temporal priority queues, entity intent horizons,
and adaptive multi-rate time advances without artificial modulo gates.
"""
from dataclasses import dataclass, field
from enum import Enum
import heapq
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

@dataclass(order=True)
class TemporalEvent:
    """Deterministic, priority-ordered temporal event."""
    scheduled_tick: int
    priority: int = 50                          # Lower value = higher execution priority
    sequence_id: int = 0                        # Monotonic counter for deterministic tie-breaking
    event_type: str = field(compare=False, default="GENERIC_EVENT")
    target_id: Optional[str] = field(compare=False, default=None)
    payload: Dict[str, Any] = field(compare=False, default_factory=dict)
    callback_service: Optional[str] = field(compare=False, default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheduled_tick": self.scheduled_tick,
            "priority": self.priority,
            "sequence_id": self.sequence_id,
            "event_type": self.event_type,
            "target_id": self.target_id,
            "payload": self.payload,
            "callback_service": self.callback_service
        }

@dataclass
class IntentHorizon:
    """Represents an agent's continuous temporal action commitment."""
    action_name: str
    started_tick: int
    duration_ticks: int
    target_destination: Optional[str] = None
    can_interrupt: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def until_tick(self) -> int:
        return self.started_tick + self.duration_ticks

    def is_active(self, current_tick: int) -> bool:
        return current_tick < self.until_tick

    def remaining_ticks(self, current_tick: int) -> int:
        return max(0, self.until_tick - current_tick)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_name": self.action_name,
            "started_tick": self.started_tick,
            "duration_ticks": self.duration_ticks,
            "until_tick": self.until_tick,
            "target_destination": self.target_destination,
            "can_interrupt": self.can_interrupt,
            "metadata": self.metadata
        }

class HierarchicalTemporalScheduler:
    """
    Min-heap priority event scheduler coordinating asynchronous deliberation,
    intent horizon expirations, and adaptive time fast-forwarding.
    """
    _instance: Optional["HierarchicalTemporalScheduler"] = None

    @classmethod
    def get_instance(cls) -> "HierarchicalTemporalScheduler":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._event_queue: List[TemporalEvent] = []
        self._sequence_counter: int = 0
        self.cancelled_event_ids: Set[int] = set()
        self.total_events_dispatched: int = 0

    def clear(self) -> None:
        self._event_queue.clear()
        self._sequence_counter = 0
        self.cancelled_event_ids.clear()
        self.total_events_dispatched = 0
        self.cancelled_event_ids.clear()
        self.total_events_dispatched = 0

    def schedule_event(
        self,
        scheduled_tick: int,
        event_type: str,
        target_id: Optional[str] = None,
        priority: int = 50,
        payload: Optional[Dict[str, Any]] = None,
        callback_service: Optional[str] = None
    ) -> TemporalEvent:
        """Schedules a temporal event deterministically into the min-heap."""
        self._sequence_counter += 1
        event = TemporalEvent(
            scheduled_tick=scheduled_tick,
            priority=priority,
            sequence_id=self._sequence_counter,
            event_type=event_type,
            target_id=target_id,
            payload=payload or {},
            callback_service=callback_service
        )
        heapq.heappush(self._event_queue, event)
        return event

    def peek_next_tick(self) -> Optional[int]:
        """Returns the tick timestamp of the earliest due event, or None if empty."""
        while self._event_queue and self._event_queue[0].sequence_id in self.cancelled_event_ids:
            heapq.heappop(self._event_queue)
        return self._event_queue[0].scheduled_tick if self._event_queue else None

    def pop_due_events(self, current_tick: int) -> List[TemporalEvent]:
        """Pops and returns all events scheduled at or before current_tick."""
        due: List[TemporalEvent] = []
        while self._event_queue:
            top = self._event_queue[0]
            if top.sequence_id in self.cancelled_event_ids:
                heapq.heappop(self._event_queue)
                continue
            if top.scheduled_tick <= current_tick:
                event = heapq.heappop(self._event_queue)
                due.append(event)
                self.total_events_dispatched += 1
            else:
                break
        return due

    def cancel_events_for_target(self, target_id: str, event_type: Optional[str] = None) -> int:
        """Cancels pending scheduled events for a specific target entity."""
        cancelled = 0
        for event in self._event_queue:
            if event.target_id == target_id:
                if event_type is None or event.event_type == event_type:
                    if event.sequence_id not in self.cancelled_event_ids:
                        self.cancelled_event_ids.add(event.sequence_id)
                        cancelled += 1
        return cancelled

    @property
    def pending_count(self) -> int:
        return len([e for e in self._event_queue if e.sequence_id not in self.cancelled_event_ids])
