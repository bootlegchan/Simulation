from typing import Any, Dict, Optional

class Blackboard:
    """Scoped context storage for NPC decision-making."""

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def clear(self) -> None:
        self._data.clear()
