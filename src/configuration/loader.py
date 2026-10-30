import json
from pathlib import Path
from typing import Any, Dict, Union
from src.core.errors import ConfigurationError
from src.configuration.validator import SchemaValidator

class ContentLoader:
    """Discovers and loads JSON configurations and manifests."""

    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.loaded_data: Dict[str, Any] = {
            "settings": {},
            "settlements": {},
            "npcs": {},
            "objects": {},
            "items": {},
            "recipes": {},
            "factions": {},
            "offices": {},
            "laws": {},
            "urban_planning": {},
            "placement_rules": {},
            "building_blueprints": {},
            "mutation_rules": {},
            "civic_crisis_policies": {},
            "subsystems_manifest": {},
        }

    def load_content(self, scenario_filename: str = "oakwood_baseline.json") -> Dict[str, Any]:
        self._load_schemas()
        
        scenario_path = self.data_dir / "scenarios" / scenario_filename
        if not scenario_path.exists():
            raise ConfigurationError(f"Scenario manifest not found: {scenario_path}")

        with open(scenario_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # 1. Load Settings
        settings_rel = manifest.get("settings_path", manifest.get("settings", "settings/simulation_config.json"))
        settings_path = self.data_dir / settings_rel
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                self.loaded_data["settings"] = json.load(f)

        # 2. Load Settlements
        for s_rel in manifest.get("settlements", []):
            s_path = self.data_dir / s_rel
            if s_path.exists():
                with open(s_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.loaded_data["settlements"][data["id"]] = data

        # 3. Load Items
        items_path = self.data_dir / "items" / "items.json"
        if items_path.exists():
            with open(items_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
                if isinstance(raw_items, dict):
                    for i_id, i_val in raw_items.items():
                        if isinstance(i_val, dict) and "id" not in i_val:
                            i_val["id"] = i_id
                        self.loaded_data["items"][i_val.get("id", i_id)] = i_val
                elif isinstance(raw_items, list):
                    for item in raw_items:
                        self.loaded_data["items"][item["id"]] = item

        # 4. Load Recipes
        recipes_path = self.data_dir / "production" / "recipes.json"
        if recipes_path.exists():
            with open(recipes_path, "r", encoding="utf-8") as f:
                raw_recipes = json.load(f)
                if isinstance(raw_recipes, dict):
                    for r_id, r_val in raw_recipes.items():
                        if isinstance(r_val, dict) and "id" not in r_val:
                            r_val["id"] = r_id
                        self.loaded_data["recipes"][r_val.get("id", r_id)] = r_val
                elif isinstance(raw_recipes, list):
                    for r in raw_recipes:
                        self.loaded_data["recipes"][r["id"]] = r

        # 5. Load Factions & Offices
        factions_path = self.data_dir / "factions" / "factions.json"
        if factions_path.exists():
            with open(factions_path, "r", encoding="utf-8") as f:
                raw_factions = json.load(f)
                if isinstance(raw_factions, dict):
                    for f_id, f_val in raw_factions.items():
                        if isinstance(f_val, dict) and "id" not in f_val:
                            f_val["id"] = f_id
                        self.loaded_data["factions"][f_val.get("id", f_id)] = f_val
                elif isinstance(raw_factions, list):
                    for fac in raw_factions:
                        self.loaded_data["factions"][fac["id"]] = fac

        offices_path = self.data_dir / "civic" / "offices.json"
        if offices_path.exists():
            with open(offices_path, "r", encoding="utf-8") as f:
                raw_offices = json.load(f)
                if isinstance(raw_offices, dict):
                    for o_id, o_val in raw_offices.items():
                        if isinstance(o_val, dict) and "id" not in o_val:
                            o_val["id"] = o_id
                        self.loaded_data["offices"][o_val.get("id", o_id)] = o_val
                elif isinstance(raw_offices, list):
                    for off in raw_offices:
                        self.loaded_data["offices"][off["id"]] = off

        # 6. Load Objects
        for o_rel in manifest.get("objects", []):
            o_path = self.data_dir / o_rel
            if o_path.exists():
                with open(o_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.loaded_data["objects"][data["id"]] = data

        # 7. Load NPCs
        for n_rel in manifest.get("npcs", []):
            n_path = self.data_dir / n_rel
            if n_path.exists():
                with open(n_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.loaded_data["npcs"][data["id"]] = data

        # 8. Load Urban Planning Config
        urban_path = self.data_dir / "settings" / "urban_planning_config.json"
        if urban_path.exists():
            with open(urban_path, "r", encoding="utf-8") as f:
                self.loaded_data["urban_planning"] = json.load(f)

        # 9. Load Object Placement Rules
        placement_path = self.data_dir / "settings" / "object_placement_rules.json"
        if placement_path.exists():
            with open(placement_path, "r", encoding="utf-8") as f:
                self.loaded_data["placement_rules"] = json.load(f)

        # 10. Load Building Blueprints
        blueprints_path = self.data_dir / "buildings" / "blueprints.json"
        if blueprints_path.exists():
            with open(blueprints_path, "r", encoding="utf-8") as f:
                self.loaded_data["building_blueprints"] = json.load(f)

        # 11. Load Building Mutation Rules
        mutation_path = self.data_dir / "settings" / "building_mutation_rules.json"
        if mutation_path.exists():
            with open(mutation_path, "r", encoding="utf-8") as f:
                self.loaded_data["mutation_rules"] = json.load(f)

        # 12. Load Civic Crisis Policies
        civic_path = self.data_dir / "settings" / "civic_crisis_policies.json"
        if civic_path.exists():
            with open(civic_path, "r", encoding="utf-8") as f:
                self.loaded_data["civic_crisis_policies"] = json.load(f)

        # 13. Load Subsystems Manifest
        subsystems_path = self.data_dir / "settings" / "subsystems_manifest.json"
        if subsystems_path.exists():
            with open(subsystems_path, "r", encoding="utf-8") as f:
                self.loaded_data["subsystems_manifest"] = json.load(f)

        # 14. Auto-discover and load any remaining JSON settings in data/settings/
        settings_dir = self.data_dir / "settings"
        if settings_dir.exists():
            for sf in settings_dir.glob("*.json"):
                stem = sf.stem
                if stem not in self.loaded_data:
                    with open(sf, "r", encoding="utf-8") as f:
                        self.loaded_data[stem] = json.load(f)

        return self.loaded_data

    def _load_schemas(self) -> None:
        schema_dir = self.data_dir / "schemas"
        if not schema_dir.exists():
            return
        for schema_file in schema_dir.glob("*.schema.json"):
            with open(schema_file, "r", encoding="utf-8") as f:
                self.schemas[schema_file.stem] = json.load(f)
