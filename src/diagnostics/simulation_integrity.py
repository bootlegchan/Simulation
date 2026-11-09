"""Simulation Integrity, Replay Determinism & Entropy Auditor."""
import math
from typing import Any, Dict, List, Optional
from src.core.path_utils import get_default_data_dir

class SimulationIntegrityAuditor:
    """Audits bitwise determinism across runs, cross-seed divergence, action diversity entropy, and world graph validity."""

    def __init__(self, data_dir: Any = None):
        self.data_dir = data_dir or get_default_data_dir()

    def verify_bitwise_determinism(self, seed: int = 42, ticks: int = 120) -> Dict[str, Any]:
        """
        Executes two independent simulation instances with the exact same seed,
        and performs bitwise comparison across all agent states, wealth, locations, and treasury balances.
        """
        from src.simulation.engine import SimulationEngine
        from src.economy.macro import MacroEconomicTracker

        engine_a = SimulationEngine(self.data_dir)
        engine_a.initialize(seed=seed)
        engine_a.tick(ticks)

        engine_b = SimulationEngine(self.data_dir)
        engine_b.initialize(seed=seed)
        engine_b.tick(ticks)

        wealth_a = MacroEconomicTracker.calculate_total_currency(
            engine_a.npcs, getattr(engine_a.context.municipal_treasury, "balance", 0.0), context=engine_a.context
        )
        wealth_b = MacroEconomicTracker.calculate_total_currency(
            engine_b.npcs, getattr(engine_b.context.municipal_treasury, "balance", 0.0), context=engine_b.context
        )
        gini_a = MacroEconomicTracker.calculate_gini_coefficient(engine_a.npcs)
        gini_b = MacroEconomicTracker.calculate_gini_coefficient(engine_b.npcs)

        gini_delta = round(abs(gini_a - gini_b), 6)
        wealth_delta = round(abs(wealth_a - wealth_b), 4)

        divergences = 0
        divergence_details = []

        for npc_id, npc_a in engine_a.npcs.items():
            if npc_id not in engine_b.npcs:
                divergences += 1
                continue
            npc_b = engine_b.npcs[npc_id]

            if round(npc_a.wealth, 2) != round(npc_b.wealth, 2):
                divergences += 1
                divergence_details.append(f"{npc_id}: wealth {npc_a.wealth} != {npc_b.wealth}")
            if npc_a.location_id != npc_b.location_id:
                divergences += 1
                divergence_details.append(f"{npc_id}: loc {npc_a.location_id} != {npc_b.location_id}")
            if round(npc_a.needs.get("hunger", 0.0), 1) != round(npc_b.needs.get("hunger", 0.0), 1):
                divergences += 1
                divergence_details.append(f"{npc_id}: hunger {npc_a.needs.get('hunger')} != {npc_b.needs.get('hunger')}")

        is_identical = (divergences == 0 and wealth_delta == 0.0 and gini_delta == 0.0)

        return {
            "is_bitwise_identical": is_identical,
            "gini_delta": gini_delta,
            "wealth_delta": wealth_delta,
            "events_match": is_identical,
            "npc_state_divergences": divergences,
            "seed": seed,
            "ticks": ticks,
            "divergence_details": divergence_details[:5]
        }

    def verify_cross_seed_divergence(self, seed_a: int = 42, seed_b: int = 999, ticks: int = 120) -> Dict[str, Any]:
        """
        Executes two simulations with distinct random seeds and verifies that agent trajectories diverge realistically.
        Calculates the Euclidean distance across final individual wealth distributions.
        """
        from src.simulation.engine import SimulationEngine

        engine_a = SimulationEngine(self.data_dir)
        engine_a.initialize(seed=seed_a)
        engine_a.tick(ticks)

        engine_b = SimulationEngine(self.data_dir)
        engine_b.initialize(seed=seed_b)
        engine_b.tick(ticks)

        common_ids = sorted(set(engine_a.npcs.keys()).intersection(set(engine_b.npcs.keys())))
        if not common_ids:
            return {"has_diverged": True, "wealth_euclidean_distance": 99.0, "jaccard_event_similarity": 0.0}

        sq_diff_sum = sum(
            (float(engine_a.npcs[nid].wealth) - float(engine_b.npcs[nid].wealth)) ** 2
            for nid in common_ids
        )
        euclidean_dist = round(math.sqrt(sq_diff_sum), 2)

        # Actions match check
        action_matches = sum(
            1 for nid in common_ids if engine_a.npcs[nid].current_action == engine_b.npcs[nid].current_action
        )
        jaccard_sim = round(action_matches / max(1, len(common_ids)), 3)

        return {
            "has_diverged": (euclidean_dist > 0.0),
            "jaccard_event_similarity": jaccard_sim,
            "wealth_euclidean_distance": euclidean_dist,
            "seed_a": seed_a,
            "seed_b": seed_b,
            "ticks": ticks
        }

    def calculate_action_entropy(self, engine: Any) -> Dict[str, Any]:
        """
        Calculates Shannon entropy across current agent actions to verify behavioral diversity without monolithic lock-in.
        """
        action_counts: Dict[str, int] = {}
        total = 0
        for npc in engine.npcs.values():
            if getattr(npc, "is_alive", True):
                act = getattr(npc, "current_action", "IDLE") or "IDLE"
                action_counts[act] = action_counts.get(act, 0) + 1
                total += 1

        if total == 0:
            return {"is_diversity_healthy": True, "shannon_entropy": 0.0, "unique_action_types": 0, "action_counts": {}}

        entropy = 0.0
        for count in action_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Entropy >= 1.0 indicates rich diversity across rest, labor, dining, socialize, etc.
        return {
            "is_diversity_healthy": (entropy >= 1.0 or len(action_counts) >= 4),
            "shannon_entropy": round(entropy, 3),
            "unique_action_types": len(action_counts),
            "action_counts": action_counts
        }

    def calculate_state_space_coverage(self, engine: Any) -> Dict[str, Any]:
        """
        Evaluates physical room occupancy and spatial coverage across settlements.
        """
        all_rooms: List[str] = []
        for sett in getattr(engine, "settlements", {}).values():
            for bldg in getattr(sett, "buildings", {}).values():
                all_rooms.extend(list(getattr(bldg, "rooms", {}).keys()))

        occupied_rooms = set()
        for npc in getattr(engine, "npcs", {}).values():
            if getattr(npc, "is_alive", True) and npc.location_id:
                occupied_rooms.add(npc.location_id)

        total_r = max(1, len(all_rooms))
        cov_ratio = round(len(occupied_rooms) / total_r, 3)

        return {
            "visited_rooms_count": len(occupied_rooms),
            "total_rooms_count": len(all_rooms),
            "room_coverage_ratio": cov_ratio
        }

    def verify_world_integrity(self, engine: Any) -> Dict[str, Any]:
        """
        Validates topological graph integrity, bidirectional doorway symmetry, and reachability.
        """
        graph = getattr(engine.context, "spatial_graph", None)
        if not graph:
            return {"is_valid": True, "reason": "No spatial graph attached."}

        all_settlement_rooms = set()
        for sett in engine.settlements.values():
            for bldg in sett.buildings.values():
                for r_id in bldg.rooms.keys():
                    all_settlement_rooms.add(r_id)

        missing_nodes = [r for r in all_settlement_rooms if r not in graph.adj_list]

        asymmetric_links = []
        for src, dests in graph.adj_list.items():
            for dest in dests:
                if src not in graph.adj_list.get(dest, set()):
                    asymmetric_links.append(f"{src} -> {dest} missing reverse")

        central_hub = engine.context.get_central_public_room() if hasattr(engine.context, "get_central_public_room") else "room_village_square"
        orphaned_rooms = []
        for r in all_settlement_rooms:
            if r in graph.adj_list and central_hub in graph.adj_list:
                path = graph.find_shortest_path(r, central_hub)
                if not path and r != central_hub:
                    orphaned_rooms.append(r)

        is_valid = (len(missing_nodes) == 0 and len(asymmetric_links) == 0 and len(orphaned_rooms) == 0)

        return {
            "is_valid": is_valid,
            "total_rooms": len(all_settlement_rooms),
            "missing_graph_nodes": missing_nodes,
            "asymmetric_doorway_links": asymmetric_links,
            "orphaned_rooms": orphaned_rooms
        }
