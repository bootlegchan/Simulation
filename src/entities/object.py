"""Interactive Objects in physical rooms."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.base import BaseEntity

class InteractiveObject(BaseEntity):
    """World object with functional capabilities and affordances."""

    def __init__(
        self,
        object_id: str,
        name: str,
        capabilities: Optional[List[str]] = None,
        location_id: Optional[str] = None,
        is_locked: bool = False,
        durability: float = 100.0,
        contained_item_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(object_id, name, "object", location_id, metadata or {})
        self.capabilities: List[str] = list(capabilities or [])
        self.is_locked: bool = is_locked
        self.durability: float = durability
        self.contained_item_ids: List[str] = list(contained_item_ids or [])

    def has_capability(self, cap: str) -> bool:
        cap_l = cap.lower()
        return any(cap_l == c.lower() or cap_l in c.lower() for c in self.capabilities)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "capabilities": self.capabilities,
            "is_locked": self.is_locked,
            "durability": self.durability,
            "contained_item_ids": self.contained_item_ids
        })
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractiveObject":
        return cls(
            object_id=data.get("id", data.get("object_id", "obj")),
            name=data.get("name", "Object"),
            capabilities=data.get("capabilities", []),
            location_id=data.get("location_id"),
            is_locked=data.get("is_locked", False),
            durability=float(data.get("durability", 100.0)),
            contained_item_ids=data.get("contained_item_ids", []),
            metadata=data.get("metadata", {})
        )
