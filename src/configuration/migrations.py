"""Schema Evolution & Migration Engine."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class DeclarativeTransformSpec:
    from_version: str
    to_version: str
    renames: Dict[str, str] = field(default_factory=dict)
    injected_defaults: Dict[str, Any] = field(default_factory=dict)

class SchemaMigrationEngine:
    """Executes schema evolution transforms across legacy dictionaries."""

    def __init__(self):
        self.specs: List[DeclarativeTransformSpec] = [
            DeclarativeTransformSpec(
                from_version="1.0.0",
                to_version="1.2.0",
                renames={"morality": "moral_erosion"},
                injected_defaults={"status_tags": {}, "chronotype_bias": "BALANCED_SOLAR"}
            )
        ]

    def migrate(self, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        res = dict(data)
        for spec in self.specs:
            if spec.from_version == from_version and spec.to_version == to_version:
                for old_k, new_k in spec.renames.items():
                    if old_k in res:
                        res[new_k] = res.pop(old_k)
                for def_k, def_v in spec.injected_defaults.items():
                    res.setdefault(def_k, def_v)
        return res
