"""Base entity abstraction."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class BaseEntity:
    id: str
    name: str
    entity_type: str
    location_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "location_id": self.location_id,
            "metadata": self.metadata
        }
