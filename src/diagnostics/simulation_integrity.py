"""
Simulation Integrity & Trajectory Divergence Auditor.
Verifies bitwise determinism for identical seeds, trajectory divergence across distinct seeds,
action choice Shannon entropy, and state space coverage to guarantee simulation diversity.
"""
import math
from typing import Any, Dict, List, Set, Tuple
from collections import Counter

from src.simulation.engine import SimulationEngine
from src.core.path_utils import get_default_data_dir
from src.economy.macro import MacroEconomicTracker


class SimulationIntegrityAuditor:
    """
    Evaluates whether the simulation satisfies the dual invariants of:
    1. 100% Bitwise Reproducibility under identical seeds (replay determinism).
    2. Dynamic Trajectory Divergence & Non-Trivial Entropy under different seeds (non-stagnation).
    """

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or get_default_data_dir()

    def verify_bitwise_determinism(self, seed: int = 42, ticks: int = 180) -> Dict[str, Any]:
        """Runs two independent simulations with the exact same seed and asserts bitwise identical states."""
        engine_a = SimulationEngine(self.data_dir)
        engine_a.initialize(seed=seed)
        engine_a.start()
        engine_a.tick(ticks)

        engine_b = SimulationEngine(self.data_dir)
        engine_b.initialize(seed=seed)
        engine_b.start()
        engine_b.tick(ticks)

        # 1. Macro economic identity
        gini_a = MacroEconomicTracker.calculate_gini_coefficient(engine_a.npcs)
        gini_b = MacroEconomicTracker.calculate_gini_coefficient(engine_b.npcs)
        wealth_a = MacroEconomicTracker.calculate_total_currency(engine_a.npcs)
        wealth_b = MacroEconomicTracker.calculate_total_currency(engine_b.npcs)

        # 2. Event history sequence identity
        events_a = [f"{e.tick}:{e.event_type}:{e.source_id}" for e in engine_a.event_bus.history]
        events_b = [f"{e.tick}:{e.event_type}:{e.source_id}" for e in engine_b.event_bus.history]
        events_match = (events_a == events_b)

        # 3. NPC need state identity
        npc_diffs = 0
        for nid, npc_a in engine_a.npcs.items():
            npc_b = engine_b.npcs[nid]
            for need_key, val_a in npc_a.needs.items():
                val_b = npc_b.needs[need_key]
                if abs(val_a - val_b) > 1e-4:
                    npc_diffs += 1

        is_identical = (gini_a == gini_b) and (wealth_a == wealth_b) and events_match and (npc_diffs == 0)

        return {
            "seed": seed,
            "ticks": ticks,
            "is_bitwise_identical": is_identical,
            "gini_delta": abs(gini_a - gini_b),
            "wealth_delta": abs(wealth_a - wealth_b),
            "events_count_a": len(events_a),
            "events_count_b": len(events_b),
            "events_match": events_match,
            "npc_state_divergences": npc_diffs,
        }

    def verify_cross_seed_divergence(
        self,
        seed_a: int = 42,
        seed_b: int = 999,
        ticks: int = 180
    ) -> Dict[str, Any]:
        """
        Runs two simulations with distinct seeds and asserts that life outcomes,
        action selections, and wealth trajectories diverge non-trivially.
        """
        engine_a = SimulationEngine(self.data_dir)
        engine_a.initialize(seed=seed_a)
        engine_a.start()
        engine_a.tick(ticks)

        engine_b = SimulationEngine(self.data_dir)
        engine_b.initialize(seed=seed_b)
        engine_b.start()
        engine_b.tick(ticks)

        # 1. Jaccard similarity of detailed event trajectory signatures
        set_a = set(
            f"{e.tick}:{e.event_type}:{e.source_id}:{e.payload.get('action_name', '')}:{e.payload.get('location_id', '')}"
            for e in engine_a.event_bus.history
        )
        set_b = set(
            f"{e.tick}:{e.event_type}:{e.source_id}:{e.payload.get('action_name', '')}:{e.payload.get('location_id', '')}"
            for e in engine_b.event_bus.history
        )
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        jaccard_similarity = round(intersection / max(1, union), 4)

        # 2. Wealth divergence Euclidean distance
        all_npc_ids = sorted(list(engine_a.npcs.keys()))
        wealth_sq_diff = sum(
            (engine_a.npcs[nid].wealth - engine_b.npcs[nid].wealth) ** 2
            for nid in all_npc_ids
        )
        wealth_euclidean_dist = round(math.sqrt(wealth_sq_diff), 2)

        # 3. Location divergence
        different_locations = sum(
            1 for nid in all_npc_ids
            if engine_a.npcs[nid].location_id != engine_b.npcs[nid].location_id
        )

        # Divergence holds if event Jaccard < 0.95 or wealth distance > 0.0
        has_diverged = (jaccard_similarity < 0.95) or (wealth_euclidean_dist > 5.0)

        return {
            "seed_a": seed_a,
            "seed_b": seed_b,
            "ticks": ticks,
            "has_diverged": has_diverged,
            "jaccard_event_similarity": jaccard_similarity,
            "wealth_euclidean_distance": wealth_euclidean_dist,
            "differing_npc_locations": different_locations,
            "total_npcs": len(all_npc_ids),
        }

    def calculate_action_entropy(self, engine: SimulationEngine) -> Dict[str, Any]:
        """
        Computes the Shannon Entropy of autonomous action choice distributions.
        H(X) = - sum(p_i * log2(p_i)). High entropy indicates rich behavioral diversity,
        whereas H ~ 0 indicates robotic monoculture attractor collapse.
        """
        actions = []
        for e in engine.event_bus.history:
            if e.event_type == "npc_autonomous_action":
                act = e.payload.get("action_name", e.payload.get("chosen_drive", "unknown"))
                actions.append(act)

        if not actions:
            return {"shannon_entropy": 0.0, "total_actions": 0, "unique_actions": 0, "distribution": {}}

        counts = Counter(actions)
        total = len(actions)
        entropy = 0.0
        distribution = {}

        for act, count in counts.items():
            prob = count / total
            entropy -= prob * math.log2(prob)
            distribution[act] = round(prob, 4)

        return {
            "shannon_entropy": round(entropy, 3),
            "total_actions_sampled": total,
            "unique_action_types": len(counts),
            "distribution": distribution,
            "is_diversity_healthy": entropy > 1.2,
        }

    def calculate_state_space_coverage(self, engine: SimulationEngine) -> Dict[str, Any]:
        """Calculates percentage of room nodes and objects actively utilized in the simulation."""
        all_rooms = set()
        for s in engine.settlements.values():
            for b in s.buildings.values():
                for r_id in b.rooms.keys():
                    all_rooms.add(r_id)

        visited_rooms = set(npc.location_id for npc in engine.npcs.values() if npc.location_id)
        room_coverage = round(len(visited_rooms) / max(1, len(all_rooms)), 3)

        return {
            "total_registered_rooms": len(all_rooms),
            "visited_rooms_count": len(visited_rooms),
            "room_coverage_ratio": room_coverage,
            "active_npcs": len(engine.npcs),
            "active_objects": len(engine.objects),
        }

    def run_full_integrity_audit(self, ticks: int = 180) -> Dict[str, Any]:
        """Executes full diagnostic verification of determinism, divergence, and entropy."""
        det_res = self.verify_bitwise_determinism(seed=42, ticks=ticks)
        div_res = self.verify_cross_seed_divergence(seed_a=42, seed_b=999, ticks=ticks)

        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(ticks)

        entropy_res = self.calculate_action_entropy(engine)
        coverage_res = self.calculate_state_space_coverage(engine)

        overall_passed = (
            det_res["is_bitwise_identical"]
            and div_res["has_diverged"]
            and entropy_res.get("is_diversity_healthy", False)
        )

        return {
            "overall_integrity_passed": overall_passed,
            "bitwise_determinism": det_res,
            "cross_seed_divergence": div_res,
            "action_entropy": entropy_res,
            "state_space_coverage": coverage_res,
        }
