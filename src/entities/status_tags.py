"""Status tags and mixin for conditioned entities."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Set

class TagScope(Enum):
    PHYSICAL = "PHYSICAL"
    PSYCHOLOGICAL = "PSYCHOLOGICAL"
    SOCIAL = "SOCIAL"
    LEGAL = "LEGAL"

@dataclass
class StatusTag:
    tag_id: str
    name: str
    scope: TagScope
    stat_modifiers: Dict[str, float] = field(default_factory=dict)
    duration_ticks: Optional[int] = None
    created_tick: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "scope": self.scope.value,
            "stat_modifiers": self.stat_modifiers,
            "duration_ticks": self.duration_ticks,
            "created_tick": self.created_tick
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusTag":
        scope_str = data.get("scope", "PHYSICAL")
        return cls(
            tag_id=data.get("tag_id", data.get("id", "tag")),
            name=data.get("name", "Tag"),
            scope=TagScope(scope_str) if isinstance(scope_str, str) else TagScope.PHYSICAL,
            stat_modifiers=data.get("stat_modifiers", {}),
            duration_ticks=data.get("duration_ticks"),
            created_tick=data.get("created_tick", 0)
        )

class TaggedEntityMixin:
    def __init__(self):
        self.status_tags: Dict[str, StatusTag] = {}
        self.tags: Set[str] = set()

    def add_status_tag(self, tag: Any) -> None:
        if isinstance(tag, str):
            self.tags.add(tag)
        else:
            self.status_tags[tag.tag_id] = tag
            self.tags.add(tag.tag_id)

    def remove_status_tag(self, tag_id: str) -> None:
        self.status_tags.pop(tag_id, None)
        self.tags.discard(tag_id)

    def add_tag(self, tag_id: str) -> None:
        self.tags.add(tag_id)

    def remove_tag(self, tag_id: str) -> None:
        self.tags.discard(tag_id)

    def has_tag(self, tag_id: str) -> bool:
        return tag_id in self.tags or tag_id in self.status_tags
