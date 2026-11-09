"""Item definitions and instances."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ItemDefinition:
    id: str
    name: str
    category: str = "GENERAL"
    base_value: float = 1.0
    weight: float = 1.0
    freshness_decay_rate: float = 0.0
    durability_decay_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "base_value": self.base_value,
            "weight": self.weight,
            "freshness_decay_rate": self.freshness_decay_rate,
            "durability_decay_rate": self.durability_decay_rate,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemDefinition":
        return cls(
            id=data.get("id", "item"),
            name=data.get("name", "Item"),
            category=data.get("category", "GENERAL"),
            base_value=float(data.get("base_value", data.get("price", 1.0))),
            weight=float(data.get("weight", 1.0)),
            freshness_decay_rate=float(data.get("freshness_decay_rate", 0.0)),
            durability_decay_rate=float(data.get("durability_decay_rate", 0.0)),
            metadata=data.get("metadata", {})
        )

@dataclass
class ItemInstance:
    instance_id: str
    item_def_id: str
    freshness: float = 100.0
    durability: float = 100.0
    quality: float = 1.0
    owner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "item_def_id": self.item_def_id,
            "freshness": round(self.freshness, 1),
            "durability": round(self.durability, 1),
            "quality": round(self.quality, 2),
            "owner_id": self.owner_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemInstance":
        return cls(
            instance_id=data.get("instance_id", "inst"),
            item_def_id=data.get("item_def_id", "item"),
            freshness=float(data.get("freshness", 100.0)),
            durability=float(data.get("durability", 100.0)),
            quality=float(data.get("quality", 1.0)),
            owner_id=data.get("owner_id"),
            metadata=data.get("metadata", {})
        )
