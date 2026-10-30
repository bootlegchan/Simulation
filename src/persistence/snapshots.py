import json
from pathlib import Path
from typing import Any, Dict

class SnapshotManager:
    """Atomic file snapshot save and restore controller."""

    @staticmethod
    def save_snapshot_file(snapshot_data: Dict[str, Any], filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_file = filepath.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2)
        temp_file.replace(filepath)

    @staticmethod
    def load_snapshot_file(filepath: Path) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
