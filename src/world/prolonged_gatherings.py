"""Prolonged Communal Gatherings, Tournaments, Conclaves, and Festivals."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Any, Dict, List, Optional
import uuid

class GatheringType(str, Enum):
    GUILD_CONCLAVE = "GUILD_CONCLAVE"
    VILLAGE_TOURNAMENT = "VILLAGE_TOURNAMENT"
    THEATRICAL_PAGEANT = "THEATRICAL_PAGEANT"
    SOLSTICE_FESTIVAL = "SOLSTICE_FESTIVAL"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

@dataclass
class GatheringDefinition:
    gathering_type: str
    name: str
    description: str = ""
    duration_ticks: int = 240
    attendee_capacity: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gathering_type": self.gathering_type,
            "name": self.name,
            "description": self.description,
            "duration_ticks": self.duration_ticks,
            "attendee_capacity": self.attendee_capacity
        }

class GatheringRegistry:
    """Central registry of public gatherings and civic festivals."""
    _instance: Optional["GatheringRegistry"] = None

    @classmethod
    def get_instance(cls) -> "GatheringRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.definitions: Dict[str, GatheringDefinition] = {
            "GUILD_CONCLAVE": GatheringDefinition("GUILD_CONCLAVE", "Quarterly Guildmasters Trade Conclave"),
            "VILLAGE_TOURNAMENT": GatheringDefinition("VILLAGE_TOURNAMENT", "Grand Settlement Athletics & Bocce Tournament"),
            "THEATRICAL_PAGEANT": GatheringDefinition("THEATRICAL_PAGEANT", "Epic Folk Ballad & Theatrical Pageant"),
            "SOLSTICE_FESTIVAL": GatheringDefinition("SOLSTICE_FESTIVAL", "Midsummer Solstice Festival"),
        }

    def register_gathering(self, definition: GatheringDefinition) -> None:
        self.definitions[definition.gathering_type.upper()] = definition

    def get_gathering(self, g_type: Any) -> Optional[GatheringDefinition]:
        gt_str = g_type.value if hasattr(g_type, "value") else str(g_type)
        return self.definitions.get(gt_str.upper())
