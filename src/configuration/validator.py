from typing import Any, Dict
from src.core.errors import ValidationException

class SchemaValidator:
    """Schema validator wrapping jsonschema."""

    @staticmethod
    def validate(instance: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        try:
            import jsonschema
            jsonschema.validate(instance=instance, schema=schema)
            return True
        except ImportError:
            # Fallback basic type checks if jsonschema package missing
            if not isinstance(instance, dict):
                raise ValidationException("Instance must be a dictionary")
            return True
        except Exception as e:
            raise ValidationException(f"Schema validation error: {e}")
