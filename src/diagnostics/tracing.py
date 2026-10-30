from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class DecisionTrace:
    tick: int
    npc_id: str
    selected_goal: str
    plan_action_names: List[str]

class DecisionTracer:
    """Decision tracing for AI debugging."""

    def __init__(self):
        self.traces: List[DecisionTrace] = []

    def record(self, tick: int, npc_id: str, goal: str, actions: List[str]) -> None:
        self.traces.append(DecisionTrace(tick, npc_id, goal, actions))
