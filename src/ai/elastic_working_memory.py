"""Elastic Cognitive Working Memory & Salience Queue Engine with Thinking Ability Scaling."""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
from src.entities.npc import NPC

class CognitiveLoadState(Enum):
    CALM_EXPANDED = "CALM_EXPANDED"
    FOCUSED_BALANCED = "FOCUSED_BALANCED"
    BURDENED_NARROWED = "BURDENED_NARROWED"
    ACUTE_TUNNEL = "ACUTE_TUNNEL"

class CopingOrientation(Enum):
    ROUTINE_GROUNDING = "ROUTINE_GROUNDING"
    DOMESTIC_SANCTUARY = "DOMESTIC_SANCTUARY"
    COMMUNITY_FELLOWSHIP = "COMMUNITY_FELLOWSHIP"
    CONTEMPLATIVE_SERENITY = "CONTEMPLATIVE_SERENITY"
    COMPULSIVE_VICE = "COMPULSIVE_VICE"

@dataclass
class CognitiveCapacityProfile:
    npc_id: str
    base_capacity: float = 60.0
    base_slots: int = 4
    current_bandwidth: float = 60.0
    available_slots: int = 4
    load_state: CognitiveLoadState = CognitiveLoadState.FOCUSED_BALANCED
    coping_orientation: CopingOrientation = CopingOrientation.ROUTINE_GROUNDING

class ElasticWorkingMemoryEngine:
    def __init__(self):
        self.profiles: Dict[str, CognitiveCapacityProfile] = {}

    def get_or_create_profile(self, npc: NPC) -> CognitiveCapacityProfile:
        if npc.id in self.profiles:
            return self.profiles[npc.id]
        from src.ai.attentional_mindspace import AttentionalMindspaceEngine
        mind_prof = AttentionalMindspaceEngine.get_instance().resolve_thinking_profile(npc)
        prof = CognitiveCapacityProfile(
            npc_id=npc.id,
            base_capacity=round(60.0 * mind_prof.deliberation_bandwidth, 1),
            base_slots=mind_prof.working_memory_capacity,
            current_bandwidth=round(60.0 * mind_prof.deliberation_bandwidth, 1),
            available_slots=mind_prof.working_memory_capacity
        )
        self.profiles[npc.id] = prof
        return prof

    def evaluate_live_bandwidth(self, npc: NPC, current_tick: int = 0) -> CognitiveCapacityProfile:
        prof = self.get_or_create_profile(npc)
        stress = float(npc.get_feeling("stress"))
        hunger = float(npc.needs.get("hunger", 0.0))
        fatigue = 100.0 - float(npc.needs.get("energy", 100.0))

        drag = (stress * 0.35) + (hunger * 0.25) + (fatigue * 0.25)
        bandwidth = max(5.0, min(100.0, prof.base_capacity - drag))
        prof.current_bandwidth = round(bandwidth, 1)

        slot_ratio = bandwidth / max(10.0, prof.base_capacity)
        calc_slots = max(1, min(prof.base_slots, int(math.ceil(prof.base_slots * slot_ratio))))
        prof.available_slots = calc_slots

        if slot_ratio >= 0.75:
            prof.load_state = CognitiveLoadState.CALM_EXPANDED
        elif slot_ratio >= 0.45:
            prof.load_state = CognitiveLoadState.FOCUSED_BALANCED
        elif slot_ratio >= 0.20:
            prof.load_state = CognitiveLoadState.BURDENED_NARROWED
        else:
            prof.load_state = CognitiveLoadState.ACUTE_TUNNEL

        return prof

    def filter_active_salience_queue(self, npc: NPC, candidate_utilities: Dict[str, float], context: Any, current_tick: int) -> Tuple[Dict[str, float], Dict[str, Any]]:
        prof = self.evaluate_live_bandwidth(npc, current_tick)
        slots = prof.available_slots

        sorted_cands = sorted(candidate_utilities.items(), key=lambda x: x[1], reverse=True)
        admitted = dict(sorted_cands[:slots])
        return admitted, {"slots": slots, "load_state": prof.load_state.value}
