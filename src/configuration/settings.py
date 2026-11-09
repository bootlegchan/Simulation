"""Central Settings Registry and Declarative Configuration Cache."""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from src.core.path_utils import get_default_data_dir

class SettingsRegistry:
    """Provides cached, declarative access to all data/settings/*.json configurations."""
    _instance: Optional["SettingsRegistry"] = None

    @classmethod
    def get_instance(cls) -> "SettingsRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, settings_dir: Optional[Path] = None):
        self.settings_dir = Path(settings_dir or (get_default_data_dir() / "settings"))
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.reload_all()

    def reload_all(self) -> None:
        self._cache.clear()
        if self.settings_dir.exists():
            for f in self.settings_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        self._cache[f.stem] = json.load(fp)
                except Exception:
                    pass

    def get(self, setting_name: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if setting_name not in self._cache:
            file_p = self.settings_dir / f"{setting_name}.json"
            if file_p.exists():
                try:
                    with open(file_p, "r", encoding="utf-8") as fp:
                        self._cache[setting_name] = json.load(fp)
                except Exception:
                    return default or {}
            else:
                return default or {}
        return self._cache.get(setting_name, default or {})

    def set_override(self, setting_name: str, data: Dict[str, Any]) -> None:
        self._cache[setting_name] = data
