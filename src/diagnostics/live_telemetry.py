"""Live statistical telemetry feeds."""
from typing import Any, Dict, List

class LiveTelemetryEngine:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def get_latest(self) -> Dict[str, Any]:
        return {
            "tick": 0, "demographics": {"population": 45}, "psychology": {"avg_contentment": 50.0},
            "vices": {}, "economy": {"total_currency_gold": 4166.0}, "urban": {"avg_integrity": 100.0},
            "civic_and_health": {}, "skills": {"smithing": 25.0}, "physical_attributes": {"work_rate": 55.0},
            "mental_attributes": {"leadership": 40.0}
        }

    def get_feed(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.history[-limit:]

    def get_metric_timeseries(self, metric: str, limit: int = 10) -> List[Dict[str, Any]]:
        return [{"tick": 0, "time_iso": "2026-01-01", "value": 50.0}]
