"""Personalized Dynamic Chronotypes and Vocational Shifts."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class Chronotype(Enum):
    EARLY_LARK = "EARLY_LARK"
    BALANCED_SOLAR = "BALANCED_SOLAR"
    NIGHT_OWL = "NIGHT_OWL"

class DailyRhythmPhase(Enum):
    DAWN_DOMESTIC_AWAKENING = "DAWN_DOMESTIC_AWAKENING"
    COMMUTE_TO_WORK = "COMMUTE_TO_WORK"
    PRODUCTIVE_LABOR_SHIFT = "PRODUCTIVE_LABOR_SHIFT"
    MIDDAY_RESPITE = "MIDDAY_RESPITE"
    AFTERNOON_SHIFT = "AFTERNOON_SHIFT"
    DUSK_COMMUTE_HOME = "DUSK_COMMUTE_HOME"
    EVENING_COMMUNAL_LEISURE = "EVENING_COMMUNAL_LEISURE"
    NOCTURNAL_WIND_DOWN = "NOCTURNAL_WIND_DOWN"
    SOMATIC_SLEEP_CONSOLIDATION = "SOMATIC_SLEEP_CONSOLIDATION"

@dataclass
class NPCPersonalRhythmProfile:
    npc_id: str
    chronotype: Chronotype
    preferred_wake_hour: float
    preferred_sleep_hour: float
    active_phase: DailyRhythmPhase = DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT
    overtime_active: bool = False

class DynamicDailyRhythmEngine:
    def __init__(self):
        self.profiles: Dict[str, NPCPersonalRhythmProfile] = {}

    def get_or_create_profile(self, npc: Any) -> NPCPersonalRhythmProfile:
        if npc.id in self.profiles:
            return self.profiles[npc.id]
        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()
        shift = occ_reg.get_shift_window(getattr(npc, "occupation", ""))
        bias = occ_reg.get_chronotype_bias(getattr(npc, "occupation", ""))
        chrono = Chronotype(bias) if bias in Chronotype._value2member_map_ else Chronotype.BALANCED_SOLAR

        # Calculate wake and sleep hours dynamically from vocational shift
        wake_h = (shift.base_start_hour - 1.5) % 24.0
        sleep_h = (shift.base_start_hour + shift.standard_duration_hours + 4.5) % 24.0

        prof = NPCPersonalRhythmProfile(
            npc_id=npc.id,
            chronotype=chrono,
            preferred_wake_hour=round(wake_h, 1),
            preferred_sleep_hour=round(sleep_h, 1)
        )
        self.profiles[npc.id] = prof
        return prof

    def evaluate_current_phase(self, npc: Any, current_tick: int, context: Optional[Any] = None) -> DailyRhythmPhase:
        prof = self.get_or_create_profile(npc)
        hour = context.clock.current_virtual_time.hour if context and hasattr(context, "clock") and context.clock else (current_tick // 60) % 24
        energy = npc.needs.get("energy", 100.0) if hasattr(npc, "needs") else 100.0

        # 1. Biological Emergency Exhaustion override
        if energy < 15.0:
            prof.active_phase = DailyRhythmPhase.SOMATIC_SLEEP_CONSOLIDATION
            return prof.active_phase

        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()
        shift = occ_reg.get_shift_window(getattr(npc, "occupation", ""))

        # 2. Check Active Surge Requisitions (e.g. Extra Bartender, Emergency Deputy Watchman)
        demand_eng = context.get_service("workplace_labor_demand_engine") if context and hasattr(context, "get_service") else None
        if demand_eng and hasattr(demand_eng, "active_requisitions"):
            for req in demand_eng.active_requisitions.values():
                if req.is_active and req.assigned_npc_id == npc.id:
                    if energy >= 20.0:
                        prof.active_phase = DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT
                        return prof.active_phase

        # 3. Scheduled Vocational Shift
        if shift.is_within_shift(hour) and energy >= 18.0:
            prof.active_phase = DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT
            return prof.active_phase

        # 4. Overtime Window
        if shift.is_overtime_window(hour) and energy >= 30.0:
            if demand_eng:
                wants_ot, mult, _ = demand_eng.evaluate_worker_overtime_choice(npc, shift, context, is_surge_job=False)
                if wants_ot:
                    prof.overtime_active = True
                    prof.active_phase = DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT
                    return prof.active_phase
            prof.overtime_active = False

        # 5. Commute / Awakening Window (1 to 2 hours before shift start)
        hours_before_shift = (shift.base_start_hour - hour) % 24.0
        if 0.0 < hours_before_shift <= 1.0:
            prof.active_phase = DailyRhythmPhase.COMMUTE_TO_WORK
            return prof.active_phase
        elif 1.0 < hours_before_shift <= 2.0:
            prof.active_phase = DailyRhythmPhase.DAWN_DOMESTIC_AWAKENING
            return prof.active_phase

        # 6. Post-Shift Decompression & Communal Leisure
        hours_after_shift = (hour - shift.end_hour) % 24.0
        if 0.0 <= hours_after_shift < 3.0:
            prof.active_phase = DailyRhythmPhase.EVENING_COMMUNAL_LEISURE if hours_after_shift >= 1.0 else DailyRhythmPhase.MIDDAY_RESPITE
            return prof.active_phase

        # 7. Sleep Window (when off-duty and stamina depleted)
        # Night workers (Guards/Smugglers): sleep during day (e.g. 06:00 to 14:00)
        # Day workers (Carpenters/Farmers): sleep at night (e.g. 22:00 to 06:00)
        hours_to_next_shift = (shift.base_start_hour - hour) % 24.0
        if 2.0 < hours_to_next_shift <= 10.0 and energy <= 80.0:
            prof.active_phase = DailyRhythmPhase.SOMATIC_SLEEP_CONSOLIDATION
            return prof.active_phase

        prof.active_phase = DailyRhythmPhase.NOCTURNAL_WIND_DOWN
        return prof.active_phase

    def process_sleep_memory_consolidation(self, npc: Any, tick: int, context: Any) -> None:
        pass
