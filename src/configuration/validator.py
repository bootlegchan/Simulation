"""Schema Validator for content packs."""
from typing import Any, Dict

class SchemaValidator:
    """Lightweight referential and property validator."""

    @classmethod
    def validate(cls, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        req = schema.get("required", [])
        for r in req:
            if r not in data:
                return False
        return True
