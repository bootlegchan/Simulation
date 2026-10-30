from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class RoutineBlock:
    start_hour: int
    end_hour: int
    activity: str
    target_location_id: Optional[str] = None

class NPCSchedule:
    """Time-based NPC daily routine blocks."""

    def __init__(self):
        self.blocks: List[RoutineBlock] = [
            RoutineBlock(0, 6, "sleep"),
            RoutineBlock(6, 8, "eat"),
            RoutineBlock(8, 17, "work"),
            RoutineBlock(17, 20, "socialize"),
            RoutineBlock(20, 24, "sleep"),
        ]

    def get_current_activity(self, hour: int) -> str:
        for block in self.blocks:
            if block.start_hour <= hour < block.end_hour:
                return block.activity
        return "idle"
