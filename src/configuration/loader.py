"""RFC 7396 Merge Patching, Defensive Data Guard, and Kahn's Topological Pack Loader."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.errors import ConfigurationError

def apply_json_merge_patch(target: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(target, dict) or not isinstance(patch, dict):
        return patch

    for key, value in patch.items():
        if value is None:
            if key in target:
                del target[key]
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = apply_json_merge_patch(target[key], value)
        else:
            target[key] = value
    return target

class DefensiveDataGuard:
    def safe_load_json(self, file_path: Path) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.exists():
            return {}
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

class ContentLoader:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.guard = DefensiveDataGuard()
        self.loaded_data: Dict[str, Any] = {}
        self.loaded_packs: Dict[str, Any] = {}
        self.schemas: Dict[str, Any] = {}

    def topological_sort_packs(self, pack_metas: Dict[str, Dict[str, Any]]) -> List[str]:
        in_degree: Dict[str, int] = {p_id: 0 for p_id in pack_metas}
        adj_list: Dict[str, List[str]] = {p_id: [] for p_id in pack_metas}

        for p_id, meta in pack_metas.items():
            deps = meta.get("dependencies", [])
            for dep in deps:
                if dep not in pack_metas:
                    raise ConfigurationError(f"Pack '{p_id}' has missing dependencies: '{dep}' not found.")
                adj_list[dep].append(p_id)
                in_degree[p_id] += 1

        queue = [p_id for p_id, deg in in_degree.items() if deg == 0]
        sorted_packs = []
        while queue:
            curr = queue.pop(0)
            sorted_packs.append(curr)
            for neighbor in adj_list.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_packs) != len(pack_metas):
            raise ConfigurationError("Circular dependency detected in content pack hierarchy.")
        return sorted_packs

    def load_content(self, scenario_filename: str = "oakwood_baseline.json", use_cache: bool = False) -> Dict[str, Any]:
        scen_p = self.data_dir / "scenarios" / scenario_filename
        if not scen_p.exists():
            scen_p = self.data_dir / scenario_filename

        scen_data = self.guard.safe_load_json(scen_p)
        merged: Dict[str, Any] = {
            "settlements": {}, "npcs": {}, "objects": {},
            "items": {}, "recipes": {}, "factions": {},
            "settings": {}, "content_packs": {}
        }

        # 1. Load settings files
        settings_dir = self.data_dir / "settings"
        if settings_dir.exists():
            for sf in settings_dir.glob("*.json"):
                merged["settings"][sf.stem] = self.guard.safe_load_json(sf)

        # 2. Ingest settlements
        if "settlements" in scen_data:
            for s_rel in scen_data["settlements"]:
                sp = self.data_dir / s_rel
                if sp.exists():
                    s_dict = self.guard.safe_load_json(sp)
                    s_id = s_dict.get("id", sp.stem)
                    merged["settlements"][s_id] = s_dict
        else:
            s_dir = self.data_dir / "settlements"
            if s_dir.exists():
                for sf in s_dir.glob("*.json"):
                    s_dict = self.guard.safe_load_json(sf)
                    s_id = s_dict.get("id", sf.stem)
                    merged["settlements"][s_id] = s_dict

        # 3. Ingest NPCs
        if "npcs" in scen_data:
            for n_rel in scen_data["npcs"]:
                np = self.data_dir / n_rel
                if np.exists():
                    n_dict = self.guard.safe_load_json(np)
                    for k, v in n_dict.items():
                        if isinstance(v, dict):
                            v.setdefault("id", k)
                            merged["npcs"][k] = v
        else:
            n_dir = self.data_dir / "npcs"
            if n_dir.exists():
                for nf in n_dir.glob("*.json"):
                    n_dict = self.guard.safe_load_json(nf)
                    for k, v in n_dict.items():
                        if isinstance(v, dict):
                            v.setdefault("id", k)
                            merged["npcs"][k] = v

        # 4. Ingest items, recipes, objects
        for cat in ("items", "recipes", "objects"):
            cat_dir = self.data_dir / cat
            if cat_dir.exists():
                for f in cat_dir.glob("*.json"):
                    item_data = self.guard.safe_load_json(f)
                    if isinstance(item_data, dict):
                        for k, v in item_data.items():
                            if isinstance(v, dict):
                                v.setdefault("id", k)
                                merged[cat][k] = v

        # 5. Discover and Mount Content Packs (only for Oakwood or if pack mounted)
        if "oakwood" in scenario_filename:
            packs_dir = self.data_dir / "packs"
            if packs_dir.exists():
                pack_metas = {}
                for pd in packs_dir.iterdir():
                    if pd.is_dir() and (pd / "pack.json").exists():
                        p_meta = self.guard.safe_load_json(pd / "pack.json")
                        p_id = p_meta.get("id", pd.name)
                        p_meta["_dir"] = pd
                        pack_metas[p_id] = p_meta

                if pack_metas:
                    order = self.topological_sort_packs(pack_metas)
                    for pid in order:
                        self.mount_pack_from_dir(pack_metas[pid]["_dir"], target_dict=merged)

        self.loaded_data = merged
        return merged

    def mount_pack_from_dir(self, pack_dir: Path, target_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target = target_dict if target_dict is not None else self.loaded_data
        pack_json = pack_dir / "pack.json"
        if not pack_json.exists():
            return {"mounted": False, "reason": "pack.json missing"}

        meta = self.guard.safe_load_json(pack_json)
        pack_id = meta.get("id", pack_dir.name)

        for asset_cat in ("items", "recipes", "npcs", "objects"):
            af = pack_dir / f"{asset_cat}.json"
            if af.exists():
                data = self.guard.safe_load_json(af)
                if isinstance(data, dict):
                    target.setdefault(asset_cat, {})
                    for k, v in data.items():
                        if isinstance(v, dict):
                            v.setdefault("id", k)
                            target[asset_cat][k] = v

        patch_file = pack_dir / "patches.json"
        if patch_file.exists():
            patches = self.guard.safe_load_json(patch_file)
            apply_json_merge_patch(target, patches)

        self.loaded_packs[pack_id] = meta
        target.setdefault("content_packs", {})[pack_id] = meta
        return {"mounted": True, "pack_id": pack_id}
