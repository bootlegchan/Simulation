from pathlib import Path

def get_project_root() -> Path:
    """Resolves absolute Path to root directory of project dynamically."""
    return Path(__file__).resolve().parent.parent.parent

def get_default_data_dir() -> Path:
    """Resolves absolute Path to default data directory dynamically."""
    return get_project_root() / "data"
