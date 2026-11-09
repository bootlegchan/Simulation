"""
Dynamic Vocational Work Shifts, Labor Demand & Elastic Overtime Engine.
Enables data-driven work hours per occupation, part-time and full-time schedules,
real-time workplace demand surges (e.g. extra bartenders on busy nights, harvest hands),
and dynamic overtime decisions modulated by fatigue, wages, and personal ambition.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

from src.entities.npc import NPC

class WorkScheduleType(Enum):
    FULL_TIME = "FULL_TIME"                 # Standard full-time shift (7-9 hours)
    PART_TIME = "PART_TIME"                 # Part-time schedule (3-5 hours)
    CASUAL_SURGE = "CASUAL_SURGE"           # On-demand surge labor (called when customer density spikes)
    FLEXIBLE_ON_DEMAND = "FLEXIBLE_ON_DEMAND" # Autonomous opportunistic work hours (scavengers, rogues)

@dataclass
class ShiftWindow:
    shift_name: str
    schedule_type: WorkScheduleType
    base_start_hour: float
    standard_duration_hours: float
    overtime_eligible: bool = True
    overtime_multiplier: float = 1.4
    max_overtime_hours: float = 4.0

    @property
    def end_hour(self) -> float:
        return (self.base_start_hour + self.standard_duration_hours) % 24.0

    @property
    def max_overtime_end_hour(self) -> float:
        return (self.base_start_hour + self.standard_duration_hours + self.max_overtime_hours) % 24.0

    def is_within_shift(self, hour: float) -> bool:
        """Determines if the given hour falls within the regular work shift, handling midnight wrap-around."""
        start = self.base_start_hour
        dur = self.standard_duration_hours
        end = (start + dur) % 24.0

        if start + dur <= 24.0:
            return start <= hour < (start + dur)
        else:
            # Wrap-around midnight (e.g. 21:00 to 05:00)
            return hour >= start or hour < end

    def is_overtime_window(self, hour: float) -> bool:
        """Determines if the given hour falls in the post-shift overtime window."""
        if not self.overtime_eligible or self.max_overtime_hours <= 0:
            return False

        start_ot = (self.base_start_hour + self.standard_duration_hours) % 24.0
        dur_ot = self.max_overtime_hours
        end_ot = (start_ot + dur_ot) % 24.0

        if start_ot + dur_ot <= 24.0:
            return start_ot <= hour < (start_ot + dur_ot)
        else:
            return hour >= start_ot or hour < end_ot

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shift_name": self.shift_name,
            "schedule_type": self.schedule_type.value,
            "base_start_hour": self.base_start_hour,
            "standard_duration_hours": self.standard_duration_hours,
            "end_hour": self.end_hour,
            "overtime_eligible": self.overtime_eligible,
            "overtime_multiplier": self.overtime_multiplier,
            "max_overtime_hours": self.max_overtime_hours,
        }

@dataclass
class WorkplaceSurgeRequisition:
    requisition_id: str
    job_title: str
    location_id: str
    reason: str
    hourly_wage_multiplier: float
    assigned_npc_id: Optional[str] = None
    created_tick: int = 0
    duration_ticks: int = 240 # Default 4-hour surge shift
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requisition_id": self.requisition_id,
            "job_title": self.job_title,
            "location_id": self.location_id,
            "reason": self.reason,
            "hourly_wage_multiplier": self.hourly_wage_multiplier,
            "assigned_npc_id": self.assigned_npc_id,
            "created_tick": self.created_tick,
            "duration_ticks": self.duration_ticks,
            "is_active": self.is_active,
        }

class WorkplaceLaborDemandEngine:
    """
    Senses real-time economic, civic, and spatial demand gradients to generate surge labor requisitions
    and calculate dynamic labor willingness without implicit hardcoded state machines.
    """
    _instance: Optional["WorkplaceLaborDemandEngine"] = None

    @classmethod
    def get_instance(cls) -> "WorkplaceLaborDemandEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.active_requisitions: Dict[str, WorkplaceSurgeRequisition] = {}
        self.surge_history: List[WorkplaceSurgeRequisition] = []

    def evaluate_workplace_surges(self, context: Any, current_tick: int) -> List[WorkplaceSurgeRequisition]:
        """
        Scans settlement facilities for real-time demand spikes:
        1. Tavern patron rush -> requisitions extra bartenders / servers.
        2. Heightened crime threat at night -> requisitions extra deputy watchmen.
        3. Low community food buffers -> requests bakery overtime prep.
        """
        new_surges: List[WorkplaceSurgeRequisition] = []
        hour = context.clock.current_virtual_time.hour if hasattr(context, "clock") and context.clock else (current_tick // 60) % 24

        # Clean expired requisitions
        for req_id in list(self.active_requisitions.keys()):
            req = self.active_requisitions[req_id]
            if current_tick - req.created_tick >= req.duration_ticks:
                req.is_active = False
                self.surge_history.append(req)
                del self.active_requisitions[req_id]

        if not hasattr(context, "npcs") or not context.npcs:
            return new_surges

        # -------------------------------------------------------------
        # 1. TAVERN HOSPITALITY DEMAND SURGE (Extra Bartenders)
        # -------------------------------------------------------------
        tavern_rooms = context.find_rooms_by_keyword("tavern") if hasattr(context, "find_rooms_by_keyword") else []
        if not tavern_rooms and hasattr(context, "find_rooms_by_keyword"):
            tavern_rooms = context.find_rooms_by_keyword("inn")
        if not tavern_rooms and hasattr(context, "find_rooms_by_building_category"):
            tavern_rooms = context.find_rooms_by_building_category("COMMERCIAL")

        for t_room in tavern_rooms:
            patrons = [n for n in context.npcs.values() if n.location_id == t_room and getattr(n, "is_alive", True)]
            patron_count = len(patrons)
            # Check how many bartenders are currently on duty
            active_barkeeps = [n for n in patrons if "innkeeper" in (n.occupation or "").lower() or "barkeeper" in (n.occupation or "").lower()]

            # If 4 or more patrons are in the tavern and active barkeeps <= 1, demand surge triggers
            req_key = f"surge_tavern_{t_room}"
            if patron_count >= 4 and len(active_barkeeps) <= 1 and req_key not in self.active_requisitions:
                surge_req = WorkplaceSurgeRequisition(
                    requisition_id=req_key,
                    job_title="Extra Bartender & Tavern Server",
                    location_id=t_room,
                    reason=f"High patron footfall ({patron_count} patrons) required surge bar assistance",
                    hourly_wage_multiplier=1.5,
                    created_tick=current_tick,
                    duration_ticks=240,
                    is_active=True
                )
                self.active_requisitions[req_key] = surge_req
                new_surges.append(surge_req)

        # -------------------------------------------------------------
        # 2. NOCTURNAL WATCH SURGE (Extra Watchmen)
        # -------------------------------------------------------------
        if (hour >= 21 or hour < 5):
            guard_rooms = context.find_rooms_by_keyword("guard") if hasattr(context, "find_rooms_by_keyword") else []
            if not guard_rooms and hasattr(context, "find_rooms_by_keyword"):
                guard_rooms = context.find_rooms_by_keyword("watch")
            if not guard_rooms and hasattr(context, "find_rooms_by_building_category"):
                guard_rooms = context.find_rooms_by_building_category("CIVIC")

            guard_room = guard_rooms[0] if guard_rooms else (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")
            req_key = "surge_night_deputy"
            active_night_guards = [n for n in context.npcs.values() if "guard" in (n.occupation or "").lower() and getattr(n, "current_action", "") in ("LABOR_WORK", "PATROL_STREETS")]
            if len(active_night_guards) < 2 and req_key not in self.active_requisitions:
                surge_req = WorkplaceSurgeRequisition(
                    requisition_id=req_key,
                    job_title="Deputy Night Watchman",
                    location_id=guard_room,
                    reason="Nocturnal street darkness required additional patrol presence",
                    hourly_wage_multiplier=1.5,
                    created_tick=current_tick,
                    duration_ticks=300,
                    is_active=True
                )
                self.active_requisitions[req_key] = surge_req
                new_surges.append(surge_req)

        return new_surges

    def evaluate_worker_overtime_choice(
        self,
        npc: NPC,
        shift_window: ShiftWindow,
        context: Any,
        is_surge_job: bool = False
    ) -> Tuple[bool, float, str]:
        """
        Intelligently evaluates whether a worker accepts an overtime shift or surge requisition.
        Balances:
          1. Somatic fatigue: Low energy drastically penalizes overtime willingness (biological brake).
          2. Financial incentive: Low wealth or high ambitious drive increases desire for surge pay.
          3. Personality traits: Conscientiousness, Ambition, and Work Rate promote overtime.
        """
        energy = float(npc.needs.get("energy", 100.0))
        # Hard somatic limit: if exhausted, worker MUST refuse overtime and seek rest
        if energy < 22.0:
            return False, 1.0, "Refused overtime due to physical exhaustion"

        wealth = float(getattr(npc, "wealth", 0.0))
        p = getattr(npc, "personality", {}) or {}
        ment = getattr(npc, "mental_attributes", {}) or {}
        phys = getattr(npc, "physical_attributes", {}) or {}

        conscientiousness = float(p.get("conscientiousness", 0.5))
        ambition = float(ment.get("ambition", 50.0)) / 100.0
        work_rate = float(phys.get("work_rate", 50.0)) / 100.0
        stress = float(npc.get_feeling("stress") if hasattr(npc, "get_feeling") else 0.0)

        # Multiplier
        mult = shift_window.overtime_multiplier if not is_surge_job else 1.5

        # Financial pressure: poorer citizens are much more eager to take extra shifts
        wealth_pressure = max(0.0, min(1.0, (30.0 - wealth) / 30.0))

        # Overall overtime willingness score (0.0 to 100.0)
        willingness = (
            (energy * 0.40) +
            (wealth_pressure * 35.0) +
            (ambition * 25.0) +
            (work_rate * 20.0) +
            (conscientiousness * 15.0) -
            (stress * 0.30)
        )

        threshold = 45.0 if not is_surge_job else 40.0
        if willingness >= threshold:
            reason = f"Accepted overtime shift with {mult:.1f}x wage premium (willingness: {willingness:.1f})"
            return True, mult, reason
        else:
            reason = f"Declined overtime to rest and preserve stamina (willingness: {willingness:.1f})"
            return False, 1.0, reason

    def find_available_surge_candidate(
        self,
        requisition: WorkplaceSurgeRequisition,
        context: Any
    ) -> Optional[NPC]:
        """Finds an eligible, available citizen to fulfill a surge labor requisition (e.g. extra bartender)."""
        candidates: List[Tuple[NPC, float]] = []
        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            # Must not already be assigned
            if npc.id == requisition.assigned_npc_id:
                continue
            # Prefer commoners, laborers, part-timers, or off-duty artisans
            occ = (npc.occupation or "").lower()
            energy = float(npc.needs.get("energy", 100.0))
            if energy < 25.0:
                continue

            affinity = 50.0
            if "commoner" in occ or "laborer" in occ or "apprentice" in occ:
                affinity += 30.0
            if "extra bartender" in requisition.job_title.lower() and any(k in occ for k in ("bard", "cook", "brewer", "commoner")):
                affinity += 25.0
            if "watch" in requisition.job_title.lower() and any(k in occ for k in ("brawler", "laborer", "guard", "veteran")):
                affinity += 25.0

            wealth_need = max(0.0, 40.0 - npc.wealth)
            score = affinity + wealth_need + (energy * 0.2)
            candidates.append((npc, score))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            chosen_npc = candidates[0][0]
            requisition.assigned_npc_id = chosen_npc.id
            return chosen_npc

        return None
