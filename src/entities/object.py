from typing import Any, Dict, List, Optional
from src.entities.base import BaseEntity

class InteractiveObject(BaseEntity):
    """Interactive object exposing capabilities (sleep, work, mill, craft, store) and lock states."""

    def __init__(
        self,
        object_id: str,
        name: str,
        capabilities: Optional[List[str]] = None,
        location_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        contained_item_ids: Optional[List[str]] = None,
        is_pantry: bool = False,
        is_locked: bool = False,
    ):
        super().__init__(object_id, name, "object", location_id)
        self.capabilities = capabilities if capabilities is not None else []
        self.owner_id = owner_id
        self.contained_item_ids = contained_item_ids if contained_item_ids is not None else []
        self.is_pantry = is_pantry
        self.is_locked = is_locked

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({
            "capabilities": self.capabilities,
            "owner_id": self.owner_id,
            "contained_item_ids": self.contained_item_ids,
            "is_pantry": self.is_pantry,
            "is_locked": self.is_locked,
        })
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractiveObject":
        return cls(
            object_id=data["id"],
            name=data["name"],
            capabilities=data.get("capabilities", []),
            location_id=data.get("location_id"),
            owner_id=data.get("owner_id"),
            contained_item_ids=data.get("contained_item_ids", []),
            is_pantry=data.get("is_pantry", False),
            is_locked=data.get("is_locked", False),
        )
