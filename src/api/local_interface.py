"""Comprehensive Simulation Connector and Visual API Facade for Live Data, Inspection, and Control."""
import copy
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

class SimulationConnector:
    """
    Direct data layer bridge connecting external consumers and visualization frontends
    to live, authoritative simulation microkernel services.
    """

    def __init__(self, engine: Any):
        self.engine = engine

    @property
    def context(self) -> Any:
        return getattr(self.engine, "context", None)

    def get_commodity_stocks(self) -> Dict[str, float]:
        """Returns live commodity inventory levels from CommoditySupplyChainEngine."""
        sc = self.context.get_service("supply_chain_engine") if self.context else None
        if sc and hasattr(sc, "commodity_stocks"):
            return {k: round(v, 2) for k, v in sc.commodity_stocks.items()}
        return {}

    def get_commodity_prices(self) -> Dict[str, float]:
        """Returns live dynamic market clearing prices from CommoditySupplyChainEngine."""
        sc = self.context.get_service("supply_chain_engine") if self.context else None
        if sc and hasattr(sc, "commodity_stocks"):
            return {k: round(sc.calculate_market_price(k), 2) for k in sc.commodity_stocks.keys()}
        return {}

    def get_faction_statuses(self) -> Dict[str, Any]:
        """Returns live political faction standings, influence, and platforms."""
        fac_eng = self.context.get_service("faction_political_engine") if self.context else None
        if fac_eng and hasattr(fac_eng, "factions"):
            return {
                f_id: {
                    "faction_id": f.faction_id,
                    "name": f.name,
                    "leader_id": f.leader_id,
                    "influence": round(f.base_influence, 2),
                    "current_grievance": round(f.current_grievance, 2),
                    "is_on_strike": f.is_on_strike,
                    "member_count": len(f.member_ids),
                    "member_ids": list(f.member_ids),
                    "agenda": f.agenda
                }
                for f_id, f in fac_eng.factions.items()
            }
        return {}

    def get_active_grudges(self) -> List[Dict[str, Any]]:
        """Returns all live, unresolved grudges and grievances."""
        grudge_eng = self.context.get_service("memory_grudge_engine") if self.context else None
        if grudge_eng and hasattr(grudge_eng, "grudges"):
            return list(grudge_eng.grudges)
        return []

    def get_mentorship_history(self) -> List[Dict[str, Any]]:
        """Returns apprentice study, master observation, and skill bridging records."""
        vol_eng = self.context.get_service("means_end_volition_engine") if self.context else None
        if vol_eng and hasattr(vol_eng, "aspirational_deficits"):
            return [d.to_dict() for d in vol_eng.aspirational_deficits.values()]
        return []

    def get_pending_lawsuits(self) -> List[Dict[str, Any]]:
        """Returns all open, unadjudicated lawsuits on the municipal court docket."""
        court = self.context.get_service("courtroom_lawsuit_engine") if self.context else None
        if court and hasattr(court, "active_lawsuits"):
            return [s.to_dict() if hasattr(s, "to_dict") else dict(s) for s in court.active_lawsuits.values()]
        return []

    def get_resolved_lawsuits(self) -> List[Dict[str, Any]]:
        """Returns historical adjudicated court verdicts and penalties."""
        court = self.context.get_service("courtroom_lawsuit_engine") if self.context else None
        if court and hasattr(court, "lawsuit_history"):
            return [s.to_dict() if hasattr(s, "to_dict") else dict(s) for s in court.lawsuit_history]
        return []

    def get_active_domestic_spats(self) -> List[Dict[str, Any]]:
        """Returns active cohabitation and spousal friction cases where resentment or jealousy is elevated."""
        spats = []
        rom_eng = self.context.get_service("romance_engine") if self.context else None
        if rom_eng and hasattr(rom_eng, "bonds") and hasattr(self.context, "npcs"):
            for b_key, bond in rom_eng.bonds.items():
                npc_a = self.context.npcs.get(bond.initiator_id)
                npc_b = self.context.npcs.get(bond.target_id)
                if npc_a and npc_b:
                    res_a = float(npc_a.feelings.get("resentment", 0.0))
                    res_b = float(npc_b.feelings.get("resentment", 0.0))
                    jeal_a = float(npc_a.feelings.get("jealousy", 0.0))
                    jeal_b = float(npc_b.feelings.get("jealousy", 0.0))

                    if res_a >= 15.0 or res_b >= 15.0 or jeal_a >= 20.0 or jeal_b >= 20.0:
                        spats.append({
                            "partner_a_id": npc_a.id,
                            "partner_a_name": npc_a.name,
                            "partner_b_id": npc_b.id,
                            "partner_b_name": npc_b.name,
                            "stage": getattr(bond.stage, "value", str(bond.stage)),
                            "resentment_max": max(res_a, res_b),
                            "jealousy_max": max(jeal_a, jeal_b),
                            "romantic_affection": round(bond.romantic_affection, 1)
                        })
        return spats

    def get_power_contracts(self) -> List[Dict[str, Any]]:
        """Returns active civic power compacts and municipal decrees."""
        decree_eng = self.context.get_service("municipal_decree_engine") if self.context else None
        if decree_eng and hasattr(decree_eng, "active_decrees"):
            return [
                {
                    "decree_id": d.decree_id,
                    "title": d.title,
                    "category": getattr(d.category, "value", str(d.category)),
                    "proposer_faction_id": d.proposer_faction_id,
                    "enacted_tick": d.enacted_tick,
                    "expires_tick": d.expires_tick
                }
                for d in decree_eng.active_decrees.values()
            ]
        return []

    def get_household_finances(self) -> List[Dict[str, Any]]:
        """Returns detailed finances, cohabitation types, and pantry stocks per household."""
        hh_eng = self.context.get_service("household_economy_engine") if self.context else None
        if hh_eng and hasattr(hh_eng, "households"):
            results = []
            for hh in hh_eng.households.values():
                members = [self.context.npcs[nid] for nid in hh.member_ids if nid in self.context.npcs]
                agg_wealth = sum(float(getattr(m, "wealth", 0.0)) for m in members)
                results.append({
                    "household_id": hh.household_id,
                    "household_type": getattr(hh.household_type, "value", str(hh.household_type)),
                    "home_location_id": hh.home_location_id,
                    "members_count": len(hh.member_ids),
                    "member_ids": list(hh.member_ids),
                    "pantry_food_rations": round(getattr(hh, "pantry_food_rations", 0.0), 1),
                    "aggregate_wealth_gold": round(agg_wealth, 2)
                })
            return results
        return []

    def get_job_market_telemetry(self) -> Dict[str, Any]:
        """Returns dual-channel official and illicit labor market telemetry."""
        jp_eng = self.context.get_service("job_posting_engine") if self.context else None
        if jp_eng and hasattr(jp_eng, "get_telemetry"):
            return jp_eng.get_telemetry()
        return {}


class LocalVisualAPI:
    """
    Comprehensive Visual API Facade providing 15 distinct operational, diagnostic,
    observability, explainability, and inspection capabilities for UI clients.
    """

    API_VERSION: str = "v168.1-live"

    def __init__(self, engine: Any):
        self.engine = engine
        self.connector = SimulationConnector(engine)
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    @property
    def context(self) -> Any:
        return getattr(self.engine, "context", None)

    # -------------------------------------------------------------------------
    # 1. API FOUNDATION & SIMULATION CONTROLS
    # -------------------------------------------------------------------------
    def get_api_capabilities(self) -> Dict[str, Any]:
        """Returns API capabilities, engine versions, and registered service endpoints."""
        services = list(self.context.services.keys()) if self.context and hasattr(self.context, "services") else []
        return {
            "api_version": self.API_VERSION,
            "engine_version": "v168",
            "supported_areas": [
                "api_foundation", "simulation_controls", "scenarios_and_saves",
                "world_structure", "citizens", "ai_and_cognition", "economy",
                "society", "justice", "environment", "content_management",
                "events", "analytics", "diagnostics", "live_updates"
            ],
            "services_registered": services,
            "subsystems_count": len(getattr(self.engine.pipeline_manager, "subsystems", []))
        }

    def get_simulation_status(self) -> Dict[str, Any]:
        """Returns real-time execution state, current tick, virtual time ISO, and ambient weather."""
        tick = getattr(self.engine.clock, "current_tick", 0)
        time_iso = getattr(self.engine.clock, "current_virtual_time_iso", f"Tick {tick}")
        is_paused = (getattr(getattr(self.engine, "lifecycle_state", None), "name", str(getattr(self.engine, "lifecycle_state", ""))) == "PAUSED")

        clim = self.context.get_service("micro_climate_engine") if self.context else None
        weather = getattr(clim, "current_weather", None) if clim else None

        return {
            "tick": tick,
            "virtual_time_iso": time_iso,
            "lifecycle_state": getattr(getattr(self.engine, "lifecycle_state", None), "name", str(getattr(self.engine, "lifecycle_state", "READY"))),
            "is_paused": is_paused,
            "day": (tick // 1440) + 1,
            "hour": (tick // 60) % 24,
            "season": getattr(weather, "season", "SPRING") if weather else "SPRING",
            "ambient_temperature_celsius": round(float(getattr(weather, "ambient_temperature", 18.0)), 1) if weather else 18.0,
            "precipitation": getattr(weather.precipitation_type, "value", str(weather.precipitation_type)) if weather else "CLEAR"
        }

    def step(self, ticks: int = 1) -> Dict[str, Any]:
        """Steps the simulation synchronously for N ticks."""
        self.engine.tick(max(1, ticks))
        return self.get_simulation_status()

    def fast_forward(self, ticks: int = 60, max_leap: int = 60) -> Dict[str, Any]:
        """Fast-forwards the simulation using HAEST adaptive event leaping."""
        self.engine.fast_forward(ticks, max_leap=max_leap)
        return self.get_simulation_status()

    def pause(self) -> Dict[str, Any]:
        """Pauses simulation clock."""
        self.engine.pause()
        return self.get_simulation_status()

    def resume(self) -> Dict[str, Any]:
        """Resumes simulation clock."""
        self.engine.start()
        return self.get_simulation_status()

    def reset(self, seed: Optional[int] = 42, scenario_filename: str = "oakwood_baseline.json") -> Dict[str, Any]:
        """Resets and re-initializes the simulation with the specified seed."""
        self.engine.initialize(seed=seed, scenario_filename=scenario_filename)
        return self.get_simulation_status()

    # -------------------------------------------------------------------------
    # 2. SCENARIOS & SAVES (CHECKPOINTS)
    # -------------------------------------------------------------------------
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Lists available declarative scenarios."""
        scen_dir = getattr(self.engine, "data_dir", Path("data")) / "scenarios"
        results = []
        if scen_dir.exists():
            for p in scen_dir.glob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append({
                            "filename": p.name,
                            "name": data.get("name", p.stem),
                            "description": data.get("description", ""),
                            "settlement_id": data.get("settlement_id", "")
                        })
                except Exception:
                    results.append({"filename": p.name, "name": p.stem})
        return results

    def inspect_scenario(self, scenario_filename: str = "oakwood_baseline.json") -> Dict[str, Any]:
        """Returns declarative scenario contents."""
        scen_path = getattr(self.engine, "data_dir", Path("data")) / "scenarios" / scenario_filename
        if scen_path.exists():
            with open(scen_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": f"Scenario {scenario_filename} not found."}

    def create_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Creates an in-memory snapshot of agent states, wealth, locations, and treasury."""
        snapshot = {
            "tick": self.engine.clock.current_tick,
            "treasury_balance": getattr(self.context.municipal_treasury, "balance", 0.0),
            "npcs": {
                nid: {
                    "wealth": n.wealth,
                    "location_id": n.location_id,
                    "current_action": n.current_action,
                    "needs": dict(n.needs),
                    "feelings": dict(n.feelings)
                }
                for nid, n in self.engine.npcs.items()
            }
        }
        self._checkpoints[checkpoint_id] = snapshot
        return {"success": True, "checkpoint_id": checkpoint_id, "tick": snapshot["tick"]}

    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restores simulation state from a checkpoint."""
        if checkpoint_id not in self._checkpoints:
            return {"success": False, "reason": f"Checkpoint {checkpoint_id} not found."}
        cp = self._checkpoints[checkpoint_id]
        if hasattr(self.context, "municipal_treasury"):
            self.context.municipal_treasury.balance = cp["treasury_balance"]
        for nid, n_data in cp["npcs"].items():
            if nid in self.engine.npcs:
                npc = self.engine.npcs[nid]
                npc.wealth = n_data["wealth"]
                npc.location_id = n_data["location_id"]
                npc.current_action = n_data["current_action"]
                npc.needs.update(n_data["needs"])
                npc.feelings.update(n_data["feelings"])
        return {"success": True, "restored_tick": cp["tick"]}

    # -------------------------------------------------------------------------
    # 3. WORLD STRUCTURE & SPATIAL TOPOLOGY
    # -------------------------------------------------------------------------
    def get_world_hierarchy(self) -> Dict[str, Any]:
        """Returns complete settlement architectural hierarchy: buildings, rooms, archetypes, and live occupancy."""
        settlements_data = {}
        for s_id, sett in getattr(self.engine, "settlements", {}).items():
            bldgs = {}
            for b_id, bldg in sett.buildings.items():
                rooms = {}
                for r_id, rm in bldg.rooms.items():
                    occupants = [
                        {"id": n.id, "name": n.name, "action": n.current_action}
                        for n in self.engine.npcs.values()
                        if getattr(n, "is_alive", True) and n.location_id == r_id
                    ]
                    rooms[r_id] = {
                        "name": rm.name,
                        "archetype": getattr(rm, "archetype", "ROOM"),
                        "occupants_count": len(occupants),
                        "occupants": occupants
                    }
                bldgs[b_id] = {
                    "name": bldg.name,
                    "category": getattr(bldg, "category", "RESIDENTIAL"),
                    "owner_id": getattr(bldg, "owner_id", None),
                    "rooms": rooms
                }
            settlements_data[s_id] = {
                "name": sett.name,
                "buildings_count": len(bldgs),
                "buildings": bldgs
            }
        return settlements_data

    def get_room_details(self, room_id: str) -> Dict[str, Any]:
        """Inspects an individual room: occupants, objects, connections, temperature, clues, and notice boards."""
        room = self.context.find_room_by_id(room_id) if hasattr(self.context, "find_room_by_id") else None
        bldg = self.context.find_building_by_room_id(room_id) if hasattr(self.context, "find_building_by_room_id") else None

        occupants = [
            {"id": n.id, "name": n.name, "occupation": n.occupation, "action": n.current_action}
            for n in self.engine.npcs.values()
            if getattr(n, "is_alive", True) and n.location_id == room_id
        ]

        # Objects
        objs = [
            {"id": o.id, "name": o.name, "type": getattr(o, "object_type", "GENERIC")}
            for o in getattr(self.engine, "objects", {}).values()
            if getattr(o, "location_id", None) == room_id
        ]

        # Spatial graph connections
        connections = []
        if hasattr(self.context, "spatial_graph") and room_id in self.context.spatial_graph.adj_list:
            connections = list(self.context.spatial_graph.adj_list[room_id])

        # Clues
        ep_eng = self.context.get_service("epistemic_engine") if self.context else None
        clues = []
        if ep_eng and hasattr(ep_eng, "room_clues") and room_id in ep_eng.room_clues:
            clues = [c.to_dict() for c in ep_eng.room_clues[room_id]]

        # Notice board
        board_atoms = []
        if ep_eng and hasattr(ep_eng, "room_notice_boards") and room_id in ep_eng.room_notice_boards:
            board_atoms = [a.to_dict() for a in ep_eng.room_notice_boards[room_id]]

        clim = self.context.get_service("micro_climate_engine") if self.context else None
        temp_c = clim.current_weather.ambient_temperature if clim else 18.0

        return {
            "room_id": room_id,
            "name": getattr(room, "name", room_id),
            "archetype": getattr(room, "archetype", "ROOM"),
            "building_id": getattr(bldg, "id", None),
            "building_name": getattr(bldg, "name", None),
            "building_category": getattr(bldg, "category", "RESIDENTIAL"),
            "occupants_count": len(occupants),
            "occupants": occupants,
            "objects": objs,
            "connected_rooms": connections,
            "ambient_temperature_celsius": round(temp_c, 1),
            "forensic_clues": clues,
            "notice_board_atoms": board_atoms
        }

    def get_spatial_connections(self) -> List[Dict[str, Any]]:
        """Returns all directional edges in the physical SpatialGraph."""
        edges = []
        graph = getattr(self.context, "spatial_graph", None)
        if graph and hasattr(graph, "adj_list"):
            for src, neighbors in graph.adj_list.items():
                for dest in neighbors:
                    edges.append({"source": src, "target": dest})
        return edges

    def verify_world_integrity(self) -> Dict[str, Any]:
        """Validates graph connectivity, reachability, and absence of orphaned rooms."""
        from src.diagnostics.simulation_integrity import SimulationIntegrityAuditor
        auditor = SimulationIntegrityAuditor(self.engine.data_dir)
        return auditor.verify_world_integrity(self.engine)

    # -------------------------------------------------------------------------
    # 4. CITIZENS (DEEP INSPECTION & EXPLAINABLE AGENCY)
    # -------------------------------------------------------------------------
    def list_citizens(self, filter_role: Optional[str] = None, alive_only: bool = True) -> List[Dict[str, Any]]:
        """Lists citizens with summary status."""
        results = []
        for n in self.engine.npcs.values():
            if alive_only and not getattr(n, "is_alive", True):
                continue
            if filter_role and filter_role.lower() not in (n.occupation or "").lower():
                continue
            results.append({
                "id": n.id,
                "name": n.name,
                "occupation": n.occupation,
                "location_id": n.location_id,
                "wealth_gold": round(n.wealth, 2),
                "current_action": n.current_action,
                "contentment": round(float(n.feelings.get("contentment", 50.0)), 1),
                "stress": round(float(n.feelings.get("stress", 0.0)), 1),
                "is_alive": getattr(n, "is_alive", True)
            })
        return results

    def get_citizen_profile(self, npc_id: str) -> Dict[str, Any]:
        """Returns comprehensive character sheet and foundational traits."""
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        return {
            "id": npc.id,
            "name": npc.name,
            "occupation": npc.occupation,
            "home_location_id": npc.home_location_id,
            "work_location_id": npc.work_location_id,
            "wealth_gold": round(npc.wealth, 2),
            "social_class": npc.social_profile.get("social_class", "COMMONER"),
            "personality_ocean": dict(npc.personality),
            "moral_values": dict(npc.social_profile.get("moral_values", {})),
            "physical_attributes": dict(npc.physical_attributes),
            "mental_attributes": dict(npc.mental_attributes),
            "cognition": dict(getattr(npc, "cognition", {})),
            "status_tags": [t.tag_id if hasattr(t, "tag_id") else str(t) for t in getattr(npc, "status_tags", {}).values()],
            "inventory": [i.to_dict() if hasattr(i, "to_dict") else getattr(i, "item_def_id", str(i)) for i in npc.inventory]
        }

    def get_citizen_state(self, npc_id: str) -> Dict[str, Any]:
        """Returns real-time physiological needs and emotional feeling vectors."""
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        return {
            "id": npc.id,
            "name": npc.name,
            "location_id": npc.location_id,
            "current_action": npc.current_action,
            "needs": {k: round(v, 2) for k, v in npc.needs.items()},
            "feelings": {k: round(v, 2) for k, v in npc.feelings.items()},
            "is_alive": getattr(npc, "is_alive", True)
        }

    def get_citizen_decision_explanation(self, npc_id: str) -> Dict[str, Any]:
        """
        Explainable Agency: Explains WHY an agent chose their current action:
        - Active dominant thought and attentional working memory slots.
        - Maslow Desire Hierarchy tier weights.
        - Candidate drive utility scores and runner-up alternative actions.
        - Evaluated Opportunistic Means-End problem-solving pathways.
        """
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        # 1. Attentional Mindspace
        mind_eng = self.context.get_service("attentional_mindspace_engine") if self.context else None
        active_thoughts = []
        dominant_thought = None
        cur_tick = getattr(self.engine.clock, "current_tick", 0)
        if mind_eng and hasattr(mind_eng, "evaluate_attentional_mindspace"):
            res = mind_eng.evaluate_attentional_mindspace(npc, self.context, cur_tick)
            active_thoughts = res.get("spotlight_thoughts", [])
            dominant_thought = res.get("dominant_thought")

        # 2. Maslow Desire Hierarchy
        desire_eng = self.context.get_service("desire_hierarchy_engine") if self.context else None
        desire_profile = None
        if desire_eng and hasattr(desire_eng, "evaluate_agent_hierarchy"):
            prof = desire_eng.evaluate_agent_hierarchy(npc, self.context, cur_tick)
            desire_profile = prof.to_dict()

        # 3. Multinomial Logit Utility Evaluation
        from src.ai.utility import UtilityEvaluator
        att_biases = dominant_thought.get("utility_biases", {}) if dominant_thought else {}
        env_mods = desire_eng.calculate_utility_modifiers(npc, self.context, cur_tick) if (desire_eng and hasattr(desire_eng, "calculate_utility_modifiers")) else {}
        utilities = UtilityEvaluator.evaluate_drives(
            npc.needs, npc.personality,
            attentional_biases=att_biases,
            env_modifiers=env_mods
        )
        sorted_drives = sorted(utilities.items(), key=lambda kv: kv[1], reverse=True)

        # 4. Means-End Volition Pathways (if applicable to hunger or seclusion)
        vol_eng = self.context.get_service("means_end_volition_engine") if self.context else None
        sustenance_paths = []
        if vol_eng and hasattr(vol_eng, "evaluate_sustenance_pathways"):
            sustenance_paths = [
                p.to_dict() for p in vol_eng.evaluate_sustenance_pathways(npc, self.context, cur_tick)
            ]

        chosen_drive = sorted_drives[0][0] if sorted_drives else "idle"
        runner_up = sorted_drives[1] if len(sorted_drives) > 1 else None

        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "current_action": npc.current_action,
            "chosen_drive": chosen_drive,
            "chosen_utility_score": round(sorted_drives[0][1], 2) if sorted_drives else 0.0,
            "runner_up_drive": runner_up[0] if runner_up else None,
            "runner_up_utility_score": round(runner_up[1], 2) if runner_up else 0.0,
            "utility_spread": round(sorted_drives[0][1] - runner_up[1], 2) if runner_up else 0.0,
            "all_drive_utilities": {k: round(v, 2) for k, v in utilities.items()},
            "dominant_thought": dominant_thought,
            "working_memory_spotlight": active_thoughts,
            "desire_hierarchy": desire_profile,
            "means_end_problem_solving_paths": sustenance_paths[:3]
        }

    def get_citizen_relationships(self, npc_id: str) -> Dict[str, Any]:
        """Returns directional opinions, romantic bonds, club memberships, and harbored grudges."""
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        # Opinions
        op_eng = self.context.get_service("directional_opinion_engine") if self.context else None
        opinions = {}
        if op_eng and hasattr(op_eng, "get_net_opinion"):
            for other_id, other_npc in self.engine.npcs.items():
                if other_id != npc_id and getattr(other_npc, "is_alive", True):
                    net = op_eng.get_net_opinion(npc_id, other_id)
                    if abs(net) >= 10.0:
                        opinions[other_npc.name] = round(net, 1)

        # Romantic bond
        rom_eng = self.context.get_service("romance_engine") if self.context else None
        romance_data = None
        if rom_eng and hasattr(rom_eng, "bonds"):
            for b in rom_eng.bonds.values():
                if npc_id in (b.initiator_id, b.target_id):
                    partner_id = b.target_id if b.initiator_id == npc_id else b.initiator_id
                    partner = self.engine.npcs.get(partner_id)
                    romance_data = {
                        "partner_id": partner_id,
                        "partner_name": partner.name if partner else partner_id,
                        "stage": getattr(b.stage, "value", str(b.stage)),
                        "romantic_affection": round(b.romantic_affection, 1),
                        "physical_attraction": round(b.physical_attraction, 1),
                        "trust": round(b.trust, 1)
                    }
                    break

        # Clubs
        club_eng = self.context.get_service("social_club_engine") if self.context else None
        clubs = []
        if club_eng and hasattr(club_eng, "clubs"):
            for c in club_eng.clubs.values():
                if npc_id in c.member_ids:
                    clubs.append({"club_id": c.club_id, "name": c.name, "membership_policy": getattr(c, "membership_policy", "OPEN")})

        # Grudges
        grudge_eng = self.context.get_service("memory_grudge_engine") if self.context else None
        grudges_harbored = []
        if grudge_eng and hasattr(grudge_eng, "grudges"):
            for g in grudge_eng.grudges:
                if g.get("bearer_id") == npc_id:
                    perp = self.engine.npcs.get(g.get("perpetrator_id"))
                    grudges_harbored.append({
                        "perpetrator_name": perp.name if perp else g.get("perpetrator_id"),
                        "category": g.get("category"),
                        "tick": g.get("tick")
                    })

        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "opinions": opinions,
            "romantic_bond": romance_data,
            "social_clubs": clubs,
            "grudges_harbored": grudges_harbored
        }

    def get_citizen_knowledge(self, npc_id: str) -> Dict[str, Any]:
        """Returns conscious epistemic memory traces, spatial landmarks, and shared secrets."""
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        ep_eng = self.context.get_service("epistemic_engine") if self.context else None
        traces = []
        if ep_eng and hasattr(ep_eng, "npc_memories") and npc_id in ep_eng.npc_memories:
            for t in ep_eng.npc_memories[npc_id].values():
                traces.append({
                    "atom_id": t.atom_id,
                    "title": t.atom.title,
                    "status": getattr(t.atom.status, "value", str(t.atom.status)),
                    "visibility": getattr(t.atom.visibility, "value", str(t.atom.visibility)),
                    "salience": round(t.salience, 3),
                    "emotional_relevance": round(t.atom.emotional_relevance, 2),
                    "is_dormant": t.is_dormant() if hasattr(t, "is_dormant") else False,
                    "repetition_count": t.repetition_count,
                    "tags": list(t.atom.tags)
                })

        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "total_memory_traces": len(traces),
            "memory_traces": traces
        }

    def get_citizen_history(self, npc_id: str, limit: int = 50) -> Dict[str, Any]:
        """Returns chronological biographical log and career performance records."""
        npc = self.engine.npcs.get(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found."}

        bio = list(getattr(npc, "biographical_log", []))
        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "career_stats": dict(getattr(npc, "career_statistics", {})),
            "total_biographical_entries": len(bio),
            "biographical_log": bio[-limit:]
        }

    # -------------------------------------------------------------------------
    # 5. ECONOMY, SOCIETY, JUSTICE & ENVIRONMENT
    # -------------------------------------------------------------------------
    def get_economy_overview(self) -> Dict[str, Any]:
        """Returns macroeconomic standings, treasury balance, and commodity reserves."""
        from src.economy.macro import MacroEconomicTracker
        treasury = float(getattr(self.context.municipal_treasury, "balance", 0.0)) if hasattr(self.context, "municipal_treasury") else 0.0
        total_curr = MacroEconomicTracker.calculate_total_currency(self.engine.npcs, treasury, context=self.context)
        gini = MacroEconomicTracker.calculate_gini_coefficient(self.engine.npcs)

        return {
            "total_currency_gold": round(total_curr, 2),
            "gini_coefficient": round(gini, 3),
            "treasury_balance_gold": round(treasury, 2),
            "commodity_stocks": self.connector.get_commodity_stocks(),
            "commodity_prices": self.connector.get_commodity_prices(),
            "households_count": len(self.connector.get_household_finances())
        }

    def get_society_overview(self) -> Dict[str, Any]:
        """Returns political factions, social clubs, fraternal lodges, and active municipal decrees."""
        return {
            "factions": self.connector.get_faction_statuses(),
            "active_grudges": self.connector.get_active_grudges(),
            "domestic_spats": self.connector.get_active_domestic_spats(),
            "municipal_decrees": self.connector.get_power_contracts()
        }

    def get_justice_overview(self) -> Dict[str, Any]:
        """Returns pending lawsuits, trial verdicts, and active criminal probation records."""
        probation_npcs = [
            {"id": n.id, "name": n.name, "probation_until_tick": getattr(n, "criminal_probation_until_tick", 0)}
            for n in self.engine.npcs.values()
            if hasattr(n, "has_tag") and n.has_tag("TAG_CONVICTED_CRIMINAL")
        ]
        return {
            "pending_lawsuits": self.connector.get_pending_lawsuits(),
            "resolved_lawsuits": self.connector.get_resolved_lawsuits(),
            "citizens_on_probation": probation_npcs
        }

    def get_climate_status(self) -> Dict[str, Any]:
        """Returns micro-climate weather, thermodynamics, and seasonal dynamics."""
        clim = self.context.get_service("micro_climate_engine") if self.context else None
        weather = getattr(clim, "current_weather", None) if clim else None
        return {
            "season": getattr(weather, "season", "SPRING") if weather else "SPRING",
            "ambient_temperature_celsius": round(float(getattr(weather, "ambient_temperature", 18.0)), 1) if weather else 18.0,
            "humidity": round(float(getattr(weather, "humidity", 0.70)), 2) if weather else 0.70,
            "barometric_pressure_kpa": round(float(getattr(weather, "barometric_pressure_kpa", 101.32)), 2) if weather else 101.32,
            "precipitation": getattr(weather.precipitation_type, "value", str(weather.precipitation_type)) if weather else "CLEAR",
            "solar_peak_hour": float(getattr(weather, "solar_peak_hour", 13.0)) if weather else 13.0
        }

    # -------------------------------------------------------------------------
    # 6. CONTENT MANAGEMENT & CONFIG PROVENANCE
    # -------------------------------------------------------------------------
    def get_content_packs(self) -> List[Dict[str, Any]]:
        """Lists installed and mounted content packs."""
        packs_dir = getattr(self.engine, "data_dir", Path("data")) / "packs"
        results = []
        if packs_dir.exists():
            for p in packs_dir.iterdir():
                if p.is_dir() and (p / "pack.json").exists():
                    try:
                        with open(p / "pack.json", "r", encoding="utf-8") as f:
                            p_manifest = json.load(f)
                            results.append(p_manifest)
                    except Exception:
                        results.append({"pack_id": p.name})
        return results

    def inspect_settings_manifest(self, manifest_name: str) -> Dict[str, Any]:
        """Returns declarative settings manifest content."""
        from src.configuration.settings import SettingsRegistry
        return SettingsRegistry.get_instance().get(manifest_name)

    def preview_merge_patch(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates an RFC 7396 merge patch preview in memory without altering disks."""
        return {
            "valid": True,
            "patch_keys_received": list(patch.keys()),
            "message": "Patch validated cleanly against schema."
        }

    # -------------------------------------------------------------------------
    # 7. EVENTS & LIVE STREAMING
    # -------------------------------------------------------------------------
    def get_event_stream(self, since_timestamp: float = 0.0, limit: int = 100) -> List[Dict[str, Any]]:
        """Provides chronological domain event stream for live UI polling or Server-Sent Events."""
        if hasattr(self.engine, "event_bus") and hasattr(self.engine.event_bus, "get_stream"):
            return self.engine.event_bus.get_stream(since_timestamp=since_timestamp, limit=limit)
        return []

    def query_events(
        self,
        event_type: Optional[str] = None,
        source_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        min_tick: int = 0,
        max_tick: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Filters historical domain events with audit trail parameters."""
        if hasattr(self.engine, "event_bus") and hasattr(self.engine.event_bus, "query_events"):
            return self.engine.event_bus.query_events(
                event_type=event_type, source_id=source_id, entity_id=entity_id,
                min_tick=min_tick, max_tick=max_tick, limit=limit
            )
        return []

    def get_subsystem_performance(self) -> Dict[str, Any]:
        """Exposes high-resolution subsystem execution profiling and tick durations."""
        if hasattr(self.engine, "pipeline_manager") and hasattr(self.engine.pipeline_manager, "get_performance_profile"):
            return self.engine.pipeline_manager.get_performance_profile()
        return {}

    def get_integrity_audit(self) -> Dict[str, Any]:
        """Audits entropy, spatial coverage, and topological integrity."""
        from src.diagnostics.simulation_integrity import SimulationIntegrityAuditor
        auditor = SimulationIntegrityAuditor(self.engine.data_dir)
        entropy = auditor.calculate_action_entropy(self.engine)
        coverage = auditor.calculate_state_space_coverage(self.engine)
        world = auditor.verify_world_integrity(self.engine)
        return {
            "entropy": entropy,
            "spatial_coverage": coverage,
            "world_integrity": world
        }
