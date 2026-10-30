from typing import Any, Dict

class SnapshotMigrator:
    """Migrates older snapshot schemas to current version."""

    @staticmethod
    def migrate(snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        version = snapshot_data.get("version", "1.0")
        if version == "1.0":
            snapshot_data["version"] = "2.0"
            snapshot_data["item_definitions"] = {}
            snapshot_data["factions"] = {}
        return snapshot_data
