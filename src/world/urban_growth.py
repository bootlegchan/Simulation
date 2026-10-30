"""
Dynamic Settlement Urban Growth, Intelligent Zoning, Path Generation & Functional Object Placement Engine.
Integrates spatial graph expansion, building condition degradation/repair, adaptive building repurposing,
and responsive civic crisis planning with 100% data-driven JSON configurations.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from src.world.model import Settlement, Building, Room, SpatialGraph
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.entities.item import ItemInstance


class BuildingCondition(Enum):
    PRISTINE = "PRISTINE"        # 85.0 - 100.0: Freshly constructed or meticulously maintained
    MAINTAINED = "MAINTAINED"    # 50.0 - 84.9: Standard condition, minor wear
    DILAPIDATED = "DILAPIDATED"  # 25.0 - 49.9: Noticeable decay, leaks, cracked walls
    CONDEMNED = "CONDEMNED"      # 1.0 - 24.9: Structural hazard, severe distress
    RUINS = "RUINS"              # 0.0: Collapsed/abandoned, squatter and crime haven


class UrbanGrowthEngine:
    """Manages dynamic zoning, road path extension, building lifecycle, and functional object placement."""

    def __init__(
        self,
        urban_planning_config: Optional[Dict[str, Any]] = None,
        placement_rules: Optional[Dict[str, Any]] = None,
        blueprints_config: Optional[Dict[str, Any]] = None,
    ):
        self.config = (urban_planning_config or {}).get("urban_planning", {})
        self.districts_cfg = self.config.get("districts", {})
        self.road_cfg = self.config.get("road_network", {})
        self.lifecycle_cfg = self.config.get("building_lifecycle", {})
        self.thresholds = self.lifecycle_cfg.get("condition_thresholds", {
            "PRISTINE": 85.0,
            "MAINTAINED": 50.0,
            "DILAPIDATED": 25.0,
            "CONDEMNED": 1.0,
            "RUINS": 0.0,
        })
        self.placement_rules = placement_rules or {}
        self.blueprints = (blueprints_config or {}).get("blueprints", {})

        # Road nodes created dynamically to extend the network
        self.active_road_nodes: Dict[str, Dict[str, Any]] = {}

    def get_condition_state(self, structural_integrity: float) -> str:
        """Evaluates structural integrity into a discrete building condition state."""
        if structural_integrity >= self.thresholds.get("PRISTINE", 85.0):
            return BuildingCondition.PRISTINE.value
        elif structural_integrity >= self.thresholds.get("MAINTAINED", 50.0):
            return BuildingCondition.MAINTAINED.value
        elif structural_integrity >= self.thresholds.get("DILAPIDATED", 25.0):
            return BuildingCondition.DILAPIDATED.value
        elif structural_integrity >= self.thresholds.get("CONDEMNED", 1.0):
            return BuildingCondition.CONDEMNED.value
        else:
            return BuildingCondition.RUINS.value

    def process_daily_lifecycle(
        self,
        settlement: Settlement,
        npcs: Dict[str, NPC],
        municipal_treasury: Any,
        current_tick: int,
        economic_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Executes daily wear-and-tear degradation, maintenance payment checks,
        and building condition updates across all settlement structures.
        """
        deg_rate = self.lifecycle_cfg.get("degradation_rate_per_day", 2.5)
        room_cost_rate = self.lifecycle_cfg.get("base_maintenance_cost_per_room", 2.0)
        repair_boost = self.lifecycle_cfg.get("repair_boost_per_cycle", 15.0)

        maintained_count = 0
        degraded_count = 0
        condemned_count = 0
        ruined_count = 0
        evicted_npc_ids = []

        for bldg_id, building in list(settlement.buildings.items()):
            room_count = max(1, len(building.rooms))
            maintenance_cost = room_count * room_cost_rate

            is_civic_or_sacred = building.category in ("CIVIC", "SACRED")
            owner = npcs.get(building.owner_id) if building.owner_id else None

            # Determine if maintenance budget is funded
            funded = False
            if is_civic_or_sacred:
                if hasattr(municipal_treasury, "balance") and municipal_treasury.balance >= maintenance_cost:
                    municipal_treasury.balance -= maintenance_cost
                    funded = True
            elif owner:
                if owner.wealth >= maintenance_cost:
                    owner.wealth -= maintenance_cost
                    funded = True
            else:
                # Common/unowned public buildings draw from treasury or general wealth
                if hasattr(municipal_treasury, "balance") and municipal_treasury.balance >= maintenance_cost:
                    municipal_treasury.balance -= maintenance_cost
                    funded = True

            if funded:
                # Structural repair & maintenance
                building.structural_integrity = min(100.0, building.structural_integrity + repair_boost)
                building.last_maintained_tick = current_tick
                maintained_count += 1
            else:
                # Wear and tear decay accelerated during economic downturns
                effective_decay = deg_rate * max(0.5, economic_multiplier)
                building.structural_integrity = max(0.0, building.structural_integrity - effective_decay)
                degraded_count += 1

            # Update condition state
            building.condition_state = self.get_condition_state(building.structural_integrity)

            # Check consequences of severe decay
            if building.condition_state == BuildingCondition.CONDEMNED.value:
                condemned_count += 1
                for r in building.rooms.values():
                    for occ_id in r.occupant_ids:
                        if occ_id in npcs:
                            npcs[occ_id].adjust_feeling("stress", 15.0)
                            npcs[occ_id].adjust_feeling("resentment", 10.0)

            elif building.condition_state == BuildingCondition.RUINS.value:
                ruined_count += 1
                # Evict occupants to village square
                for r in building.rooms.values():
                    for occ_id in list(r.occupant_ids):
                        if occ_id in npcs:
                            evicted_npc = npcs[occ_id]
                            evicted_npc.location_id = "room_village_square"
                            evicted_npc.adjust_feeling("grief", 30.0)
                            evicted_npc.adjust_feeling("stress", 40.0)
                            evicted_npc_ids.append(occ_id)
                    r.occupant_ids.clear()

        return {
            "settlement_id": settlement.id,
            "total_buildings": len(settlement.buildings),
            "maintained_count": maintained_count,
            "degraded_count": degraded_count,
            "condemned_count": condemned_count,
            "ruined_count": ruined_count,
            "evicted_npc_ids": evicted_npc_ids,
            "tick": current_tick
        }

    def determine_target_district_and_road(
        self,
        category: str,
        settlement: Settlement
    ) -> Tuple[str, str]:
        """
        Intelligently identifies the appropriate district and access road node
        for a building of a given category, preventing random scattering.
        """
        # 1. Match category to district profile
        target_district_id = "DISTRICT_RESIDENTIAL"
        for d_id, d_cfg in self.districts_cfg.items():
            if category in d_cfg.get("allowed_categories", []):
                target_district_id = d_id
                break

        d_cfg = self.districts_cfg.get(target_district_id, {})
        road_prefix = d_cfg.get("primary_road_prefix", "lane_residential")
        max_per_road = d_cfg.get("max_buildings_per_road", 4)

        # 2. Find existing road node in that district with capacity
        candidate_road_id = None
        road_occupancy: Dict[str, int] = {}

        for bldg in settlement.buildings.values():
            if bldg.district_id == target_district_id:
                for r in bldg.rooms.values():
                    for conn in r.connected_room_ids:
                        if road_prefix in conn:
                            road_occupancy[conn] = road_occupancy.get(conn, 0) + 1

        for road_id, count in road_occupancy.items():
            if count < max_per_road:
                candidate_road_id = road_id
                break

        # 3. If no road available or at capacity, generate a new road extension!
        if not candidate_road_id:
            seq = len(self.active_road_nodes) + 1
            candidate_road_id = f"room_{road_prefix}_{seq}"
            road_name = f"{d_cfg.get('name', 'Settlement')} Avenue {seq}"

            # Create road node as a dedicated circulation room
            road_bldg_id = f"bldg_road_{road_prefix}_{seq}"
            road_room = Room(
                room_id=candidate_road_id,
                name=road_name,
                building_id=road_bldg_id,
                connected_room_ids=["room_village_square"],  # Connect back to main town plaza
                archetype="ROAD_CIRCULATION"
            )

            # Ensure market square links to new road
            for bldg in settlement.buildings.values():
                if "room_village_square" in bldg.rooms:
                    bldg.rooms["room_village_square"].connected_room_ids.append(candidate_road_id)

            road_bldg = Building(
                building_id=road_bldg_id,
                name=road_name,
                settlement_id=settlement.id,
                rooms={candidate_road_id: road_room},
                category="CIRCULATION",
                district_id=target_district_id
            )
            settlement.buildings[road_bldg_id] = road_bldg
            self.active_road_nodes[candidate_road_id] = {
                "district_id": target_district_id,
                "building_id": road_bldg_id,
                "name": road_name
            }

        return target_district_id, candidate_road_id

    def place_objects_intelligently(
        self,
        room: Room,
        archetype: str,
        objects_dict: Dict[str, InteractiveObject]
    ) -> List[str]:
        """
        Places interactable objects inside rooms following data-driven anchor rules and archetype slots.
        """
        archetype_rules = self.placement_rules.get("room_archetypes", {}).get(archetype, {})
        req_slots = archetype_rules.get("required_slots", [])
        opt_slots = archetype_rules.get("optional_slots", [])
        all_target_slots = req_slots + opt_slots

        anchor_rules = self.placement_rules.get("anchor_rules", {})
        created_obj_ids = []

        for slot in all_target_slots:
            for obj_template_id, rule in anchor_rules.items():
                if rule.get("slot") == slot and archetype in rule.get("valid_archetypes", []):
                    already_placed = any(
                        objects_dict.get(oid) and objects_dict[oid].has_capability(slot)
                        for oid in room.contained_object_ids
                    )
                    if already_placed:
                        continue

                    instance_obj_id = f"obj_{slot}_{uuid.uuid4().hex[:6]}"
                    obj_name = obj_template_id.replace("object_", "").replace("_", " ").title()

                    capabilities = [slot]
                    if "hearth" in slot:
                        capabilities.extend(["family_gathering", "cook_meal"])
                    elif "sleeping" in slot:
                        capabilities.extend(["sleep", "private_intimacy"])
                    elif "desk" in slot:
                        capabilities.extend(["write_diary"])
                    elif "storage" in slot or "chest" in slot:
                        capabilities.extend(["store_items", "retrieve_items"])
                    elif "work" in slot:
                        capabilities.extend(["craft", "work"])
                    elif "board" in slot:
                        capabilities.extend(["post_bulletin", "read_bulletin"])
                    elif "triage" in slot or "sickbed" in slot:
                        capabilities.extend(["rest", "heal", "triage"])
                    elif "alarm" in slot:
                        capabilities.extend(["sound_alarm", "civic_warning", "fire_watch"])
                    elif "water" in slot:
                        capabilities.extend(["firefighting_reservoir", "water_source"])
                    elif "lantern" in slot:
                        capabilities.extend(["illuminate_street", "deter_crime"])

                    new_obj = InteractiveObject(
                        object_id=instance_obj_id,
                        name=obj_name,
                        capabilities=capabilities,
                        location_id=room.id,
                        is_locked=True if "vault" in slot or "chest" in slot else False
                    )

                    stock_item_ids = rule.get("default_stocked_items", [])
                    new_obj.contained_item_ids = list(stock_item_ids)

                    objects_dict[instance_obj_id] = new_obj
                    room.contained_object_ids.append(instance_obj_id)
                    created_obj_ids.append(instance_obj_id)
                    break

        return created_obj_ids

    def execute_intelligent_construction(
        self,
        settlement: Settlement,
        blueprint_id: str,
        spatial_graph: SpatialGraph,
        objects_dict: Dict[str, InteractiveObject],
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically constructs a building from a data-driven blueprint,
        intelligently attaching it to the appropriate district and street node,
        and placing anchored interactable objects inside each room.
        """
        blueprint = self.blueprints.get(blueprint_id)
        if not blueprint:
            return {"success": False, "reason": f"Blueprint '{blueprint_id}' not found."}

        category = blueprint.get("category", "RESIDENTIAL")
        district_id, road_node_id = self.determine_target_district_and_road(category, settlement)

        bldg_slug = blueprint.get("template_id", "building")
        new_bldg_id = f"bldg_{bldg_slug}_{uuid.uuid4().hex[:6]}"
        bldg_name = blueprint.get("name", "New Construction")

        created_rooms: Dict[str, Room] = {}
        created_room_ids: List[str] = []
        created_object_ids: List[str] = []

        room_templates = blueprint.get("room_templates", [])
        entrance_room_id = None

        for r_tmpl in room_templates:
            r_id = f"room_{bldg_slug}_{r_tmpl['id_suffix']}_{uuid.uuid4().hex[:4]}"
            r_name = r_tmpl["name"]
            r_archetype = r_tmpl.get("archetype", "LIVING_ROOM")

            room = Room(
                room_id=r_id,
                name=r_name,
                building_id=new_bldg_id,
                connected_room_ids=[],
                archetype=r_archetype
            )
            created_rooms[r_id] = room
            created_room_ids.append(r_id)

            if r_tmpl.get("is_entrance", False) and not entrance_room_id:
                entrance_room_id = r_id

            objs_placed = self.place_objects_intelligently(room, r_archetype, objects_dict)
            created_object_ids.extend(objs_placed)

        if not entrance_room_id and created_room_ids:
            entrance_room_id = created_room_ids[0]

        if entrance_room_id and road_node_id:
            created_rooms[entrance_room_id].connected_room_ids.append(road_node_id)
            for b in settlement.buildings.values():
                if road_node_id in b.rooms:
                    b.rooms[road_node_id].connected_room_ids.append(entrance_room_id)

        for r_tmpl, r_id in zip(room_templates, created_room_ids):
            internal_suffixes = r_tmpl.get("internal_connections", [])
            for target_suffix in internal_suffixes:
                for other_tmpl, other_id in zip(room_templates, created_room_ids):
                    if other_tmpl["id_suffix"] == target_suffix and other_id != r_id:
                        if other_id not in created_rooms[r_id].connected_room_ids:
                            created_rooms[r_id].connected_room_ids.append(other_id)

        building = Building(
            building_id=new_bldg_id,
            name=bldg_name,
            settlement_id=settlement.id,
            rooms=created_rooms,
            category=category,
            structural_integrity=100.0,
            condition_state=BuildingCondition.PRISTINE.value,
            district_id=district_id,
            owner_id=owner_id,
            maintenance_budget=blueprint.get("base_value", 100.0) * 0.05
        )

        settlement.buildings[new_bldg_id] = building
        spatial_graph.build_graph({settlement.id: settlement})

        return {
            "success": True,
            "building_id": new_bldg_id,
            "building_name": bldg_name,
            "category": category,
            "district_id": district_id,
            "connected_road_node_id": road_node_id,
            "rooms_created": created_room_ids,
            "objects_placed": created_object_ids,
        }

    def demolish_condemned_building(
        self,
        settlement: Settlement,
        building_id: str,
        spatial_graph: SpatialGraph,
        objects_dict: Dict[str, InteractiveObject],
        npcs: Dict[str, NPC]
    ) -> Dict[str, Any]:
        """
        Demolishes a condemned or ruined building, disconnecting room nodes
        and clearing the plot for urban redevelopment.
        """
        if building_id not in settlement.buildings:
            return {"success": False, "reason": "Building not found"}

        bldg = settlement.buildings.pop(building_id)
        cleared_room_ids = list(bldg.rooms.keys())
        cleared_object_ids = []

        for b in settlement.buildings.values():
            for r in b.rooms.values():
                r.connected_room_ids = [c for c in r.connected_room_ids if c not in cleared_room_ids]

        for r_id, room in bldg.rooms.items():
            for occ_id in room.occupant_ids:
                if occ_id in npcs:
                    npcs[occ_id].location_id = "room_village_square"
            for oid in room.contained_object_ids:
                objects_dict.pop(oid, None)
                cleared_object_ids.append(oid)

        spatial_graph.build_graph({settlement.id: settlement})

        return {
            "success": True,
            "demolished_building_id": building_id,
            "cleared_rooms": cleared_room_ids,
            "cleared_objects": cleared_object_ids,
        }


# ==============================================================================
# ADAPTIVE BUILDING REPURPOSING ENGINE
# ==============================================================================

class BuildingRepurposingEngine:
    """
    Manages functional mutations of buildings when owners face debt, poverty,
    or structural decay, converting businesses into illicit operations or squatters.
    """

    def __init__(self, mutation_rules_config: Optional[Dict[str, Any]] = None):
        self.rules = (mutation_rules_config or {}).get("mutation_rules", {})

    def evaluate_and_repurpose_building(
        self,
        building: Building,
        owner: Optional[NPC],
        settlement: Settlement,
        objects_dict: Dict[str, InteractiveObject],
        npcs: Dict[str, NPC],
        current_tick: int
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether a building's functional purpose changes due to economic
        distress, decay, or windfall prosperity.
        """
        bldg_name_lower = building.name.lower()
        bldg_id_lower = building.id.lower()

        for rule_id, rule in self.rules.items():
            target_types = rule.get("target_building_types", [])
            matches_type = False
            if "any" in target_types:
                matches_type = True
            else:
                for t in target_types:
                    if t in bldg_name_lower or t in bldg_id_lower:
                        matches_type = True
                        break

            if not matches_type:
                continue

            conds = rule.get("trigger_conditions", {})

            # Check wealth triggers
            if "owner_max_wealth" in conds:
                if not owner or owner.wealth > conds["owner_max_wealth"]:
                    continue

            if "owner_min_wealth" in conds:
                if not owner or owner.wealth < conds["owner_min_wealth"]:
                    continue

            # Check integrity triggers
            if "max_structural_integrity" in conds:
                if building.structural_integrity > conds["max_structural_integrity"]:
                    continue

            if "min_structural_integrity" in conds:
                if building.structural_integrity < conds["min_structural_integrity"]:
                    continue

            if "structural_integrity_threshold" in conds:
                if building.structural_integrity > conds["structural_integrity_threshold"]:
                    continue

            if conds.get("is_abandoned", False):
                has_occupants = any(len(r.occupant_ids) > 0 for r in building.rooms.values())
                if owner or has_occupants:
                    continue

            # If all conditions pass, execute the mutation!
            old_name = building.name
            old_category = building.category

            building.name = rule.get("new_building_name", building.name)
            building.category = rule.get("new_category", building.category)

            # Room archetype overrides
            for r_id, new_arch in rule.get("room_archetype_overrides", {}).items():
                if r_id in building.rooms:
                    building.rooms[r_id].archetype = new_arch

            # Remove unwanted objects
            removed_obj_ids = []
            for target_obj_def in rule.get("objects_to_remove", []):
                for r in building.rooms.values():
                    for oid in list(r.contained_object_ids):
                        if target_obj_def in oid or (objects_dict.get(oid) and target_obj_def in objects_dict[oid].name.lower()):
                            r.contained_object_ids.remove(oid)
                            objects_dict.pop(oid, None)
                            removed_obj_ids.append(oid)

            # Install new functional objects
            installed_obj_ids = []
            for install_spec in rule.get("objects_to_install", []):
                obj_id_pattern = install_spec.get("object_id")
                target_suffix = install_spec.get("target_room_suffix", "first")

                # Find destination room
                dest_room = None
                for r_id, r in building.rooms.items():
                    if target_suffix == "first":
                        dest_room = r
                        break
                    elif target_suffix in r_id or target_suffix in r.name.lower():
                        dest_room = r
                        break

                if not dest_room and building.rooms:
                    dest_room = list(building.rooms.values())[0]

                if dest_room:
                    new_oid = f"{obj_id_pattern}_{uuid.uuid4().hex[:6]}"
                    clean_name = obj_id_pattern.replace("object_", "").replace("_", " ").title()

                    caps = ["vice"]
                    if "gambling" in obj_id_pattern:
                        caps.extend(["gamble", "underground_betting"])
                    elif "still" in obj_id_pattern:
                        caps.extend(["distill_spirits", "brew_moonshine"])
                    elif "altar" in obj_id_pattern:
                        caps.extend(["perform_cult_rite", "worship"])
                    elif "counter" in obj_id_pattern or "fence" in obj_id_pattern:
                        caps.extend(["fence_contraband", "trade"])
                    elif "cache" in obj_id_pattern:
                        caps.extend(["store_contraband", "retrieve_items"])
                    elif "bed" in obj_id_pattern:
                        caps.extend(["sleep", "private_intimacy"])
                    elif "desk" in obj_id_pattern:
                        caps.extend(["write_diary", "accounting"])

                    new_obj = InteractiveObject(
                        object_id=new_oid,
                        name=clean_name,
                        capabilities=caps,
                        location_id=dest_room.id,
                        is_locked=True if "cache" in obj_id_pattern or "altar" in obj_id_pattern else False
                    )

                    objects_dict[new_oid] = new_obj
                    dest_room.contained_object_ids.append(new_oid)
                    installed_obj_ids.append(new_oid)

            # Apply social and psychological impact
            impact = rule.get("social_impact", {})
            if owner:
                if "owner_crime_propensity_increase" in impact:
                    owner.vices["crime_propensity"] = min(100.0, owner.vices.get("crime_propensity", 0.0) + impact["owner_crime_propensity_increase"])
                    owner.adjust_feeling("guilt", 20.0)
                    owner.adjust_feeling("stress", -10.0)  # Relief from finding illicit income

            return {
                "mutated": True,
                "building_id": building.id,
                "rule_id": rule_id,
                "old_name": old_name,
                "new_name": building.name,
                "old_category": old_category,
                "new_category": building.category,
                "installed_objects": installed_obj_ids,
                "removed_objects": removed_obj_ids,
                "tick": current_tick
            }

        return None


# ==============================================================================
# RESPONSIVE CIVIC CRISIS PLANNING ENGINE
# ==============================================================================

class ResponsiveCivicPlanningEngine:
    """
    Monitors settlement crises (fires, medical shortages, crime surges, homelessness)
    and enacts municipal urban planning interventions: emergency clinics, fire towers,
    and security checkpoints.
    """

    def __init__(
        self,
        civic_policies_config: Optional[Dict[str, Any]] = None,
        urban_growth_engine: Optional[UrbanGrowthEngine] = None
    ):
        self.policies = (civic_policies_config or {}).get("civic_crisis_policies", {})
        self.growth_engine = urban_growth_engine or UrbanGrowthEngine()
        self.resolved_crises: Set[str] = set()

    def evaluate_and_mitigate_crises(
        self,
        settlement: Settlement,
        municipal_treasury: Any,
        npcs: Dict[str, NPC],
        objects_dict: Dict[str, InteractiveObject],
        spatial_graph: SpatialGraph,
        event_history: List[Any],
        current_tick: int,
        notice_board_engine: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates world conditions against civic policies, enacting municipal emergency
        construction and notice board decrees when public health or safety is threatened.
        """
        mitigations = []

        for crisis_id, policy in self.policies.items():
            if crisis_id in self.resolved_crises:
                continue

            evaluator = policy.get("trigger_evaluator")
            is_triggered = False

            # Evaluator 1: Medical Building Deficit
            if evaluator == "MEDICAL_BUILDING_COUNT_ZERO":
                medical_count = sum(1 for b in settlement.buildings.values() if b.category == "MEDICAL")
                if medical_count == 0:
                    is_triggered = True

            # Evaluator 2: Recent Fire or Arson Destruction
            elif evaluator == "RECENT_FIRE_OR_ARSON_EVENT":
                for evt in event_history:
                    evt_type = getattr(evt, "event_type", "")
                    payload = getattr(evt, "payload", {})
                    if evt_type == "building_destroyed":
                        if "fire" in str(payload).lower() or "arson" in str(payload).lower() or payload.get("reason") in ("fire", "arson"):
                            is_triggered = True
                            break

            # Evaluator 3: Crime Density Surge
            elif evaluator == "HIGH_CRIME_DENSITY_SURGE":
                underworld_count = sum(1 for b in settlement.buildings.values() if b.category == "UNDERWORLD")
                if underworld_count >= 2:
                    is_triggered = True

            # Evaluator 4: Homeless / Displaced Population Threshold
            elif evaluator == "DISPLACED_NPC_THRESHOLD_EXCEEDED":
                displaced_count = sum(1 for n in npcs.values() if n.location_id == "room_village_square" or n.home_location_id is None)
                if displaced_count >= 2:
                    is_triggered = True

            if not is_triggered:
                continue

            # Check treasury gold requirement
            min_gold = policy.get("min_treasury_gold", 40.0)
            treasury_balance = getattr(municipal_treasury, "balance", 100.0)
            if treasury_balance < min_gold:
                continue

            # Execute Emergency Construction!
            blueprint_id = policy.get("required_blueprint")
            construct_res = self.growth_engine.execute_intelligent_construction(
                settlement=settlement,
                blueprint_id=blueprint_id,
                spatial_graph=spatial_graph,
                objects_dict=objects_dict,
                owner_id="npc_devon"  # Town Mayor owns public civic structures
            )

            if construct_res.get("success"):
                # Deduct funds from treasury
                if hasattr(municipal_treasury, "balance"):
                    municipal_treasury.balance -= min_gold

                # Post decree on town notice board if engine is present
                if notice_board_engine and hasattr(notice_board_engine, "post_bulletin"):
                    notice_board_engine.post_bulletin(
                        title=policy.get("council_order_title", "MUNICIPAL CIVIC DECREE"),
                        content=policy.get("council_order_body", "Council emergency directive enacts construction."),
                        author_npc_id="npc_devon",
                        current_tick=current_tick
                    )

                # Social relief to citizens
                relief = policy.get("social_relief", {})
                if "settlement_stress_relief" in relief:
                    for n in npcs.values():
                        n.adjust_feeling("stress", -relief["settlement_stress_relief"])
                        n.adjust_feeling("contentment", 15.0)

                self.resolved_crises.add(crisis_id)
                mitigations.append({
                    "crisis_id": crisis_id,
                    "policy_name": policy.get("description"),
                    "blueprint_constructed": blueprint_id,
                    "building_id": construct_res.get("building_id"),
                    "district_id": construct_res.get("district_id"),
                    "treasury_spent": min_gold,
                    "tick": current_tick
                })

        return mitigations
