"""Action Durations Engine."""
from typing import Any

class ActionDurationEngine:
    def calculate_duration(self, action_name: str, npc: Any, hour: int = 12, context: Any = None) -> int:
        if action_name in ("SLEEP_REST", "COLLAPSE_FATIGUE"):
            return 360  # 6 hours sleep block
        if action_name in ("LABOR_WORK", "SMELT_INGOTS", "FORGE_TOOLS"):
            return 120  # 2 hours work block
        return 60
