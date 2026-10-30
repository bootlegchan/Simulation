"""
Environmental Micro-Climates, Indoor Thermal Dynamics, and Infrastructure Sanitation Engine.
Models temperature variations, hearth heating, hypothermia, water source purity, and silt accumulation.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.world.model import Settlement, Building, Room
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.entities.item import ItemInstance


@dataclass
class RoomThermalState:
    room_id: str
    temperature_celsius: float
    has_active_hearth: bool = False
    is_indoor: bool = True
    insulation_quality: float = 1.0


class MicroClimateEngine:
    """Calculates ambient and indoor room temperatures, heating deltas, and physiological exposure."""

    def __init__(self, climate_config: Optional[Dict[str, Any]] = None):
        cfg = (climate_config or {}).get("climate_system", {})
        self.seasonal_base = cfg.get("seasonal_base_temperatures_celsius", {
            "WINTER": -5.0,
            "SPRING": 14.0,
            "SUMMER": 28.0,
            "AUTUMN": 10.0
        })
        self.diurnal_variation = cfg.get("diurnal_variation_celsius", {
            "DAWN": -4.0,
            "DAY": 5.0,
            "DUSK": -1.0,
            "NIGHT": -6.0
        })
        self.indoor_insulation_bonus = cfg.get("indoor_insulation_bonus_celsius", 12.0)
        self.hearth_heating_delta = cfg.get("hearth_heating_delta_celsius", 22.0)
        self.thresholds = cfg.get("physiological_thresholds", {
            "hypothermia_risk_celsius": 4.0,
            "freezing_damage_celsius": -2.0,
            "comfort_min_celsius": 16.0,
            "comfort_max_celsius": 24.0,
            "heat_exhaustion_celsius": 32.0
        })
        self.exposure_penalties = cfg.get("exposure_penalties", {
            "hypothermia_energy_drain_per_tick": 0.5,
            "hypothermia_stress_surge": 20.0,
            "heat_thirst_hunger_surge": 15.0
        })

    def calculate_ambient_temperature(self, season: str = "WINTER", time_of_day: Any = "DAY") -> float:
        base = self.seasonal_base.get(str(season).upper(), 10.0)
        tod_str = "DAY"
        if isinstance(time_of_day, int):
            if 6 <= time_of_day <= 8:
                tod_str = "DAWN"
            elif 9 <= time_of_day <= 18:
                tod_str = "DAY"
            elif 19 <= time_of_day <= 21:
                tod_str = "DUSK"
            else:
                tod_str = "NIGHT"
        else:
            tod_str = str(time_of_day).upper()
        diurnal = self.diurnal_variation.get(tod_str, 0.0)
        return round(base + diurnal, 1)

    def calculate_indoor_room_temperature(
        self,
        room: Room,
        building: Building,
        season: str = "WINTER",
        hour: Any = "DAY",
        objects_dict: Optional[Dict[str, InteractiveObject]] = None
    ) -> float:
        ambient = self.calculate_ambient_temperature(season, hour)
        return self.evaluate_room_temperature(room, building, ambient, objects_dict or {})

    def apply_temperature_consequences(self, npc: NPC, room_temperature: float) -> Dict[str, Any]:
        return self.apply_exposure_effects_to_npc(npc, room_temperature)

    def evaluate_room_temperature(
        self,
        room: Room,
        building: Building,
        ambient_temp: float,
        objects_dict: Dict[str, InteractiveObject]
    ) -> float:
        is_outdoor = "square" in room.id.lower() or "plaza" in room.id.lower() or "fields" in room.id.lower() or "road" in room.id.lower()
        if is_outdoor:
            return ambient_temp

        # Indoor base starts with ambient + building insulation
        condition_mult = building.structural_integrity / 100.0 if hasattr(building, "structural_integrity") else 1.0
        insulation = self.indoor_insulation_bonus * max(0.4, condition_mult)
        indoor_temp = ambient_temp + insulation

        # Check for active hearth heating
        has_hearth = any(
            objects_dict.get(oid) and (
                "hearth" in oid or
                objects_dict[oid].has_capability("primary_hearth") or
                objects_dict[oid].has_capability("family_gathering") or
                objects_dict[oid].has_capability("cook_meal")
            )
            for oid in room.contained_object_ids
        )

        if has_hearth:
            indoor_temp += self.hearth_heating_delta

        return round(indoor_temp, 1)

    def apply_exposure_effects_to_npc(self, npc: NPC, room_temperature: float) -> Dict[str, Any]:
        result = {
            "npc_id": npc.id,
            "temperature_celsius": room_temperature,
            "is_hypothermic": False,
            "is_heat_exhausted": False,
            "is_comfortable": False
        }

        if room_temperature <= self.thresholds["hypothermia_risk_celsius"]:
            result["is_hypothermic"] = True
            npc.adjust_feeling("stress", self.exposure_penalties["hypothermia_stress_surge"])
            npc.needs["energy"] = max(0.0, npc.needs.get("energy", 50.0) - 15.0)
            if room_temperature <= self.thresholds["freezing_damage_celsius"]:
                npc.adjust_feeling("grief", 15.0)
        elif room_temperature >= self.thresholds["heat_exhaustion_celsius"]:
            result["is_heat_exhausted"] = True
            npc.adjust_feeling("stress", 15.0)
            npc.needs["hunger"] = min(100.0, npc.needs.get("hunger", 20.0) + 15.0)
        elif self.thresholds["comfort_min_celsius"] <= room_temperature <= self.thresholds["comfort_max_celsius"]:
            result["is_comfortable"] = True
            npc.adjust_feeling("contentment", 10.0)

        return result


class InfrastructureSanitationEngine:
    """Manages town water source purity, silt decay, and purification."""

    def __init__(self, infrastructure_config: Optional[Dict[str, Any]] = None):
        cfg = (infrastructure_config or {}).get("infrastructure_decay", {})
        self.water_sources_cfg = cfg.get("water_sources", {})
        self.purity_thresholds = cfg.get("purity_thresholds", {
            "PRISTINE": 80.0,
            "TOLERABLE": 50.0,
            "CONTAMINATED": 25.0,
            "STAGNANT_MUCK": 0.0
        })
        self.source_states: Dict[str, Dict[str, Any]] = {}

    def get_or_register_source(self, source_id: str, source_type: str = "town_well") -> Dict[str, Any]:
        if source_id not in self.source_states:
            type_cfg = self.water_sources_cfg.get(source_type, {
                "base_purity": 100.0,
                "daily_silt_accumulation": 5.0,
                "cleaning_restoration": 50.0
            })
            self.source_states[source_id] = {
                "source_id": source_id,
                "type": source_type,
                "purity": type_cfg.get("base_purity", 100.0),
                "last_cleaned_tick": 0,
                "times_cleaned": 0
            }
        return self.source_states[source_id]

    def process_daily_infrastructure_decay(self, objects_dict: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
        for oid, obj in objects_dict.items():
            if 'well' in oid or (hasattr(obj, 'has_capability') and obj.has_capability('water_source')):
                self.get_or_register_source(oid, 'town_well')
            elif 'trough' in oid or (hasattr(obj, 'has_capability') and obj.has_capability('firefighting_reservoir')):
                self.get_or_register_source(oid, 'water_trough')
            elif 'culvert' in oid or (hasattr(obj, 'has_capability') and obj.has_capability('street_runoff')):
                self.get_or_register_source(oid, 'drainage_culvert')
        return self.process_daily_silt_accumulation(current_tick)

    def process_daily_silt_accumulation(self, current_tick: int) -> Dict[str, Any]:
        results = {}
        for s_id, state in self.source_states.items():
            type_cfg = self.water_sources_cfg.get(state["type"], {"daily_silt_accumulation": 5.0})
            decay = type_cfg.get("daily_silt_accumulation", 5.0)
            state["purity"] = max(0.0, round(state["purity"] - decay, 1))

            status = "PRISTINE"
            if state["purity"] < self.purity_thresholds["CONTAMINATED"]:
                status = "CONTAMINATED"
            elif state["purity"] < self.purity_thresholds["TOLERABLE"]:
                status = "TOLERABLE"

            results[s_id] = {
                "purity": state["purity"],
                "status": status
            }
        return results

    def purify_water_source(
        self,
        source_id: str,
        actor: NPC,
        purification_alum: Optional[ItemInstance] = None,
        current_tick: int = 0
    ) -> Dict[str, Any]:
        state = self.get_or_register_source(source_id)
        type_cfg = self.water_sources_cfg.get(state["type"], {"cleaning_restoration": 50.0})

        boost = type_cfg.get("cleaning_restoration", 50.0)
        alum_used = False
        if purification_alum and purification_alum in actor.inventory:
            actor.inventory.remove(purification_alum)
            boost += 40.0
            alum_used = True

        state["purity"] = min(100.0, round(state["purity"] + boost, 1))
        state["last_cleaned_tick"] = current_tick
        state["times_cleaned"] += 1

        actor.adjust_feeling("pride", 15.0)
        actor.adjust_feeling("contentment", 10.0)

        return {
            "success": True,
            "source_id": source_id,
            "purity_after": state["purity"],
            "alum_used": alum_used,
            "actor_id": actor.id
        }
