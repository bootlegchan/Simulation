from typing import Any, Dict, Optional

class ItemDefinition:
    """Reusable definition for item types."""

    def __init__(
        self,
        item_id: str,
        name: str,
        category: str,
        base_value: float = 10.0,
        spoil_rate: float = 0.0,
        max_durability: float = 100.0,
        is_contraband: bool = False
    ):
        self.id = item_id
        self.name = name
        self.category = category
        self.base_value = base_value
        self.spoil_rate = spoil_rate
        self.max_durability = max_durability
        self.is_contraband = is_contraband

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "base_value": self.base_value,
            "spoil_rate": self.spoil_rate,
            "max_durability": self.max_durability,
            "is_contraband": self.is_contraband,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemDefinition":
        return cls(
            item_id=data["id"],
            name=data["name"],
            category=data.get("category", "general"),
            base_value=data.get("base_value", 10.0),
            spoil_rate=data.get("spoil_rate", 0.0),
            max_durability=data.get("max_durability", 100.0),
            is_contraband=data.get("is_contraband", False),
        )

class ItemInstance:
    """Instance of an item with dynamic state (freshness, durability, quality, metadata)."""

    def __init__(
        self,
        instance_id: str,
        item_def_id: str,
        freshness: float = 100.0,
        durability: float = 100.0,
        quality: float = 1.0,
        owner_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.instance_id = instance_id
        self.item_def_id = item_def_id
        self.freshness = max(0.0, min(100.0, freshness))
        self.durability = max(0.0, min(100.0, durability))
        self.quality = max(0.5, min(3.0, quality))
        self.owner_id = owner_id
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "item_def_id": self.item_def_id,
            "freshness": self.freshness,
            "durability": self.durability,
            "quality": self.quality,
            "owner_id": self.owner_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemInstance":
        return cls(
            instance_id=data["instance_id"],
            item_def_id=data["item_def_id"],
            freshness=data.get("freshness", 100.0),
            durability=data.get("durability", 100.0),
            quality=data.get("quality", 1.0),
            owner_id=data.get("owner_id"),
            metadata=data.get("metadata", {}),
        )
