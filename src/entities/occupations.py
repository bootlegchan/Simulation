"""Occupation Registry & Declarative Vocational Skills, Shifts, and Offerings."""
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from src.core.path_utils import get_default_data_dir
from src.economy.work_shifts import ShiftWindow, WorkScheduleType

class OccupationRegistry:
    """Central registry of declarative vocations, skills, work shifts, and commercial offerings."""
    _instance: Optional["OccupationRegistry"] = None

    @classmethod
    def get_instance(cls) -> "OccupationRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.occupations: Dict[str, Dict[str, Any]] = {}
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        try:
            cfg_p = get_default_data_dir() / "settings" / "occupations.json"
            if cfg_p.exists():
                with open(cfg_p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "occupations" in data:
                        for k, v in data["occupations"].items():
                            self.occupations[k.lower()] = v
        except Exception:
            pass

    def get_occupation_spec(self, occ_title: str) -> Dict[str, Any]:
        t_l = (occ_title or "").lower()
        for k, v in self.occupations.items():
            if k in t_l:
                return v
        return self.occupations.get("commoner", {})

    def get_shift_window(self, occ_title: str) -> ShiftWindow:
        spec = self.get_occupation_spec(occ_title)
        sched_type_str = spec.get("schedule_type", "FULL_TIME")
        sched_enum = WorkScheduleType(sched_type_str) if sched_type_str in WorkScheduleType._value2member_map_ else WorkScheduleType.FULL_TIME
        return ShiftWindow(
            shift_name=spec.get("shift_name", "STANDARD_DAY"),
            schedule_type=sched_enum,
            base_start_hour=float(spec.get("base_start_hour", 8.0)),
            standard_duration_hours=float(spec.get("standard_duration_hours", 8.0)),
            overtime_eligible=bool(spec.get("overtime_eligible", True)),
            overtime_multiplier=float(spec.get("overtime_multiplier", 1.4)),
            max_overtime_hours=4.0
        )

    def get_schedule_type(self, occ_title: str) -> WorkScheduleType:
        return self.get_shift_window(occ_title).schedule_type

    def is_overtime_eligible(self, occ_title: str) -> bool:
        return self.get_shift_window(occ_title).overtime_eligible

    def get_primary_skill(self, occ_title: str) -> str:
        return self.get_occupation_spec(occ_title).get("primary_skill", "crafting")

    def get_fallback_work_location(self, occ_title: str, context: Optional[Any] = None) -> str:
        spec = self.get_occupation_spec(occ_title)
        fallback = spec.get("fallback_room")
        if fallback and context and hasattr(context, "find_room_by_id") and context.find_room_by_id(fallback):
            return fallback
        if context and hasattr(context, "get_central_public_room"):
            return context.get_central_public_room()
        return fallback or "room_village_square"

    def is_civic(self, occ_title: str) -> bool:
        return self.get_occupation_spec(occ_title).get("is_civic", False)

    def get_chronotype_bias(self, occ_title: str) -> str:
        return self.get_occupation_spec(occ_title).get("chronotype", "BALANCED_SOLAR")

    def get_food_offering(self, occ_title: str) -> Optional[Dict[str, Any]]:
        spec = self.get_occupation_spec(occ_title)
        return spec.get("food_offering")

    def get_palate_preference(self, occ_title: str) -> str:
        spec = self.get_occupation_spec(occ_title)
        return spec.get("palate_preference", "WHOLESOME_HEARTH_BREAD")

    def get_default_skills(self, occ_title: str) -> Dict[str, float]:
        primary = self.get_primary_skill(occ_title)
        try:
            from src.configuration.settings import SettingsRegistry
            occ_cfg = SettingsRegistry.get_instance().get("occupations")
            baselines = occ_cfg.get("global_skill_baselines", {})
        except Exception:
            baselines = {}

        primary_val = float(baselines.get("primary_skill_level", 65.0))
        skills = {
            "brawling": float(baselines.get("brawling", 20.0)),
            "subterfuge": float(baselines.get("subterfuge", 15.0)),
            "bargaining": float(baselines.get("bargaining", 30.0)),
            "farming": float(baselines.get("farming", 25.0)),
            "smithing": float(baselines.get("smithing", 20.0)),
            "baking": float(baselines.get("baking", 20.0)),
            "crafting": float(baselines.get("crafting", 30.0)),
            "hospitality": float(baselines.get("hospitality", 20.0))
        }
        skills[primary] = primary_val
        spec = self.get_occupation_spec(occ_title)
        if "custom_skills" in spec and isinstance(spec["custom_skills"], dict):
            skills.update({k: float(v) for k, v in spec["custom_skills"].items()})
        return skills
