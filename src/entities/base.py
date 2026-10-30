from typing import Any, Dict, Optional

class BaseEntity:
    """Base class for all identifiable domain entities."""

    def __init__(self, entity_id: str, name: str, entity_type: str, location_id: Optional[str] = None):
        self.id = entity_id
        self.name = name
        self.entity_type = entity_type
        self.location_id = location_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "location_id": self.location_id,
        }
