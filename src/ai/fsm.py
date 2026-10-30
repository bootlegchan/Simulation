from enum import Enum
from typing import Any, Dict, List, Optional

class FSMState(Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING_ACTION = "EXECUTING_ACTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class FSMController:
    """Operational state machine for plan execution."""

    def __init__(self):
        self.state = FSMState.IDLE
        self.current_plan: Optional[List[Any]] = None
        self.current_action_index = 0

    def set_plan(self, plan: List[Any]) -> None:
        self.current_plan = plan
        self.current_action_index = 0
        self.state = FSMState.EXECUTING_ACTION if plan else FSMState.COMPLETED

    def tick(self) -> FSMState:
        if self.state != FSMState.EXECUTING_ACTION or not self.current_plan:
            return self.state

        if self.current_action_index < len(self.current_plan):
            # Advance action execution
            self.current_action_index += 1
            if self.current_action_index >= len(self.current_plan):
                self.state = FSMState.COMPLETED
        return self.state
