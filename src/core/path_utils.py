"""Dynamic path resolution utilities."""
from pathlib import Path

def get_project_root() -> Path:
    """Returns absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_default_data_dir() -> Path:
    """Returns absolute path to the canonical data directory."""
    return get_project_root() / "data"
