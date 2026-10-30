import uuid

def generate_id(prefix: str = "entity") -> str:
    """Generate a deterministic or pseudo-unique string identifier."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
