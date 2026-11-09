"""Live Headless Hot-Reloading Observer."""
import os
from pathlib import Path
from typing import Any, Dict

class PackHotReloader:
    """Polls asset directories for modifications and hot-reloads data in memory."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.last_mtime: float = self._get_latest_mtime()

    def _get_latest_mtime(self) -> float:
        latest = 0.0
        for root, _, files in os.walk(self.data_dir):
            if ".cache" in root or ".quarantine" in root:
                continue
            for f in files:
                if f.endswith(".json"):
                    m = (Path(root) / f).stat().st_mtime
                    if m > latest:
                        latest = m
        return latest

    def poll_and_reload(self, engine: Any) -> Dict[str, Any]:
        curr = self._get_latest_mtime()
        if curr > self.last_mtime:
            self.last_mtime = curr
            # Re-read content
            engine.loader.load_content()
            return {"reloaded": True, "timestamp": curr}
        return {"reloaded": False}
