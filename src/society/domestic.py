from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.society.status import PrestigeCalculator

class HouseholdDynamics:
    """Manages domestic cohabitation, roommate friction, shared meals, and eviction upon breakup."""

    def __init__(self, home_location_id: str, resident_ids: List[str]):
        self.home_location_id = home_location_id
        self.resident_ids = list(resident_ids)
        self.domestic_friction_score = 0.0  # 0 to 100

    def evaluate_domestic_harmony(self, npcs: Dict[str, NPC]) -> float:
        """Calculates domestic friction based on personality mismatches and cleanliness/resource conflicts."""
        residents = [npcs[r_id] for r_id in self.resident_ids if r_id in npcs]
        if len(residents) <= 1:
            self.domestic_friction_score = 0.0
            return 0.0

        friction = 0.0
        num_pairs = 0
        for i in range(len(residents)):
            for j in range(i + 1, len(residents)):
                npc1 = residents[i]
                npc2 = residents[j]
                num_pairs += 1
                
                # Mismatched conscientiousness and openness causes housemate friction
                c_diff = abs(npc1.personality.get("conscientiousness", 0.5) - npc2.personality.get("conscientiousness", 0.5))
                o_diff = abs(npc1.personality.get("openness", 0.5) - npc2.personality.get("openness", 0.5))
                
                # Hunger/energy stress exacerbates domestic fights
                stress1 = (100.0 - npc1.needs.get("energy", 100.0)) + npc1.needs.get("hunger", 0.0)
                stress2 = (100.0 - npc2.needs.get("energy", 100.0)) + npc2.needs.get("hunger", 0.0)
                
                pair_friction = (c_diff + o_diff) * 25.0 + ((stress1 + stress2) / 10.0)
                friction += pair_friction

        avg_friction = friction / max(1, num_pairs)
        self.domestic_friction_score = round(min(100.0, avg_friction), 2)
        return self.domestic_friction_score

    def execute_cohabitation_move_in(self, npc_a: NPC, npc_b: NPC, target_home_id: str) -> None:
        """Move couple into a shared residence upon reaching COURTING or SPOUSES stage."""
        npc_a.home_location_id = target_home_id
        npc_b.home_location_id = target_home_id
        if npc_a.id not in self.resident_ids:
            self.resident_ids.append(npc_a.id)
        if npc_b.id not in self.resident_ids:
            self.resident_ids.append(npc_b.id)

    def process_breakup_and_eviction(
        self,
        npc_a: NPC,
        npc_b: NPC,
        lodging_fallback_id: str = "room_tavern_lodging"
    ) -> Dict[str, Any]:
        """Upon divorce/breakup, the lower-prestige or displaced partner is evicted to tavern lodgings."""
        prestige_a = PrestigeCalculator.calculate_prestige(npc_a)
        prestige_b = PrestigeCalculator.calculate_prestige(npc_b)

        if prestige_a >= prestige_b:
            evicted_npc = npc_b
            remaining_npc = npc_a
        else:
            evicted_npc = npc_a
            remaining_npc = npc_b

        if evicted_npc.id in self.resident_ids:
            self.resident_ids.remove(evicted_npc.id)

        # Evict to fallback lodging
        evicted_npc.home_location_id = lodging_fallback_id
        evicted_npc.current_state = "EVICTED_SEARCHING_LODGING"

        return {
            "evicted_npc_id": evicted_npc.id,
            "evicted_npc_name": evicted_npc.name,
            "remaining_npc_id": remaining_npc.id,
            "new_home_id": lodging_fallback_id,
            "prestige_evicted": min(prestige_a, prestige_b),
            "prestige_remaining": max(prestige_a, prestige_b)
        }
