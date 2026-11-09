"""Asset Binary Serialization & Fast-Boot Cache."""
import hashlib
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

class AssetCacheManager:
    """Compiles merged assets into binary cache for sub-5ms boot times."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_data_hash(self, scenario_filename: str) -> str:
        hasher = hashlib.sha256()
        for root, _, files in os.walk(self.data_dir):
            if ".cache" in root or ".quarantine" in root:
                continue
            for f in sorted(files):
                if f.endswith(".json"):
                    fp = Path(root) / f
                    hasher.update(str(fp.stat().st_mtime_ns).encode())
                    hasher.update(str(fp.stat().st_size).encode())
        hasher.update(scenario_filename.encode())
        return hasher.hexdigest()[:16]

    def get_cached_content(self, scenario_filename: str, current_hash: str) -> Optional[Dict[str, Any]]:
        stem = Path(scenario_filename).stem
        cf = self.cache_dir / f"{stem}_{current_hash}.pkl"
        if cf.exists():
            try:
                with open(cf, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None

    def store_cached_content(self, scenario_filename: str, current_hash: str, data: Dict[str, Any]) -> None:
        stem = Path(scenario_filename).stem
        cf = self.cache_dir / f"{stem}_{current_hash}.pkl"
        try:
            with open(cf, "wb") as f:
                pickle.dump(data, f)
        except Exception:
            pass
