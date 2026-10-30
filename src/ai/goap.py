import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

class Goal:
    def __init__(self, name: str, target_state: Dict[str, Any], priority: float = 1.0):
        self.name = name
        self.target_state = target_state
        self.priority = priority

class Action:
    def __init__(
        self,
        name: str,
        preconditions: Dict[str, Any],
        effects: Dict[str, Any],
        cost: float = 1.0,
    ):
        self.name = name
        self.preconditions = preconditions
        self.effects = effects
        self.cost = cost

class GOAPPlanner:
    """Optimized A* pathfinding planner for GOAP goals with priority queues and frozen state hashing."""

    @staticmethod
    def _state_key(state: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
        return tuple(sorted((k, v) for k, v in state.items()))

    @staticmethod
    def plan(
        current_state: Dict[str, Any],
        goal: Goal,
        available_actions: List[Action]
    ) -> Optional[List[Action]]:
        
        def satisfies_state(state: Dict[str, Any], target: Dict[str, Any]) -> bool:
            return all(state.get(k) == v for k, v in target.items())

        if satisfies_state(current_state, goal.target_state):
            return []

        # Priority queue for A* search: (cost, counter, state_dict, path)
        counter = 0
        queue = [(0.0, counter, current_state, [])]
        visited_states: Set[Tuple[Tuple[str, Any], ...]] = set()

        while queue:
            cost, _, state, path = heapq.heappop(queue)

            if satisfies_state(state, goal.target_state):
                return path

            key = GOAPPlanner._state_key(state)
            if key in visited_states:
                continue
            visited_states.add(key)

            for action in available_actions:
                if satisfies_state(state, action.preconditions):
                    next_state = dict(state)
                    next_state.update(action.effects)
                    next_key = GOAPPlanner._state_key(next_state)
                    if next_key not in visited_states:
                        new_cost = cost + action.cost
                        new_path = list(path)
                        new_path.append(action)
                        counter += 1
                        heapq.heappush(queue, (new_cost, counter, next_state, new_path))

        return None
