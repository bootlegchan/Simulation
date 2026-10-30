from typing import Dict, List, Any

class FestivalEvent:
    def __init__(self, event_id: str, name: str, tick_duration: int = 10):
        self.id = event_id
        self.name = name
        self.tick_duration = tick_duration

class FestivalManager:
    def __init__(self):
        self.active_event: Optional[FestivalEvent] = None

    def start_festival(self, event: FestivalEvent) -> None:
        self.active_event = event

    def is_festival_active(self) -> bool:
        return self.active_event is not None

class BardPerformance:
    @staticmethod
    def perform(bard_id: str, audience_ids: List[str]) -> Dict[str, Any]:
        return {
            "bard_id": bard_id,
            "audience_count": len(audience_ids),
            "social_boost": 25.0,
            "mood_boost": 20.0
        }
