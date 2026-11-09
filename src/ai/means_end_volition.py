"""
Opportunistic Means-End Volition & Dynamic Moral Elasticity Engine.
Operates 100% on declarative policies from data/settings/means_end_volition.json.

Models adaptive problem solving when primary conventional avenues are blocked:
1. Multi-Tier Means-End Pathways:
   - CONVENTIONAL: Approved, lawful, standard (e.g. buy food, owned bedroom, certified job).
   - COMPENSATORY: Resourceful, informal compromise (e.g. borrow food, rent tavern loft, forage, trade study).
   - TRANSGRESSIVE: Norm-violating, desperate actions (e.g. petty shoplifting, indoor trespassing, public tryst).
2. Continuous Moral Elasticity Friction:
   - Moral resistance discounts quadratically as physiological/psychological urgency surges.
   - An honorable citizen under extreme starvation (hunger > 80) or lovers under extreme passion (> 75)
     can overcome moral friction to survive or connect.
3. Aspirational Skill Bridging:
   - Skill-deficient NPCs do not discard career ambitions; they study, observe master artisans,
     and practice at community benches to bridge the deficit.
4. Closed-Loop Emotional Aftermath:
   - Transgressive relief satisfies physical tension but generates psychological guilt and stress,
     driving confession, restitution, and moral calibration.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from src.entities.npc import NPC
from src.configuration.settings import SettingsRegistry


class VolitionTier(str, Enum):
    CONVENTIONAL = "CONVENTIONAL"
    COMPENSATORY = "COMPENSATORY"
    TRANSGRESSIVE = "TRANSGRESSIVE"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None


class ProblemSolvingDomain(str, Enum):
    SUSTENANCE = "SUSTENANCE"
    COURTSHIP = "COURTSHIP"
    VOCATIONAL = "VOCATIONAL"
    SHELTER = "SHELTER"


@dataclass
class AspirationalCareerDeficit:
    npc_id: str
    target_occupation: str
    required_skill: str
    required_level: float
    current_level: float
    deficit: float
    priority_score: float = 1.0
    created_tick: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "target_occupation": self.target_occupation,
            "required_skill": self.required_skill,
            "required_level": round(self.required_level, 1),
            "current_level": round(self.current_level, 1),
            "deficit": round(self.deficit, 1),
            "priority_score": round(self.priority_score, 2),
            "created_tick": self.created_tick
        }


@dataclass
class ProblemSolvingPath:
    path_id: str
    domain: ProblemSolvingDomain
    tier: VolitionTier
    title: str
    description: str
    target_location_id: Optional[str]
    target_entity_id: Optional[str]
    moral_cost: float
    effective_viability: float
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_id": self.path_id,
            "domain": self.domain.value if hasattr(self.domain, "value") else str(self.domain),
            "tier": self.tier.value if hasattr(self.tier, "value") else str(self.tier),
            "title": self.title,
            "description": self.description,
            "target_location_id": self.target_location_id,
            "target_entity_id": self.target_entity_id,
            "moral_cost": round(self.moral_cost, 2),
            "effective_viability": round(self.effective_viability, 2),
            "payload": self.payload
        }


class MeansEndVolitionEngine:
    """
    Central Opportunistic Problem Solving & Elastic Moral Frontier Engine.
    Evaluates alternative problem-solving paths across Sustenance, Courtship, and Vocation
    when initial conventional resources are missing.
    """
    _instance: Optional["MeansEndVolitionEngine"] = None

    @classmethod
    def get_instance(cls) -> "MeansEndVolitionEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # npc_id -> AspirationalCareerDeficit
        self.aspirations: Dict[str, AspirationalCareerDeficit] = {}
        # Tracking telemetry
        self.total_compensatory_actions: int = 0
        self.total_transgressive_actions: int = 0
        self.total_aspirational_study_hours: int = 0
        self.total_shoplifting_events: int = 0
        self.total_food_borrowing_events: int = 0
        self.total_foraging_events: int = 0
        self.total_trespass_trysts: int = 0

    def clear(self) -> None:
        self.aspirations.clear()
        self.total_compensatory_actions = 0
        self.total_transgressive_actions = 0
        self.total_aspirational_study_hours = 0
        self.total_shoplifting_events = 0
        self.total_food_borrowing_events = 0
        self.total_foraging_events = 0
        self.total_trespass_trysts = 0

    def get_volition_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("means_end_volition").get("means_end_volition", {})

    # -------------------------------------------------------------------------
    # 1. Continuous Moral Elasticity Friction
    # -------------------------------------------------------------------------
    def calculate_effective_moral_resistance(
        self,
        npc: NPC,
        urgency: float,
        action_base_moral_cost: float = 35.0
    ) -> float:
        """
        Calculates the psychological moral barrier resisting a transgressive action.
        As somatic or emotional urgency increases, the resistance scales down quadratically:
        EffectiveResistance = BaseResistance / max(1.0, Urgency^2)
        """
        cfg = self.get_volition_config()
        weights = cfg.get("moral_friction_weights", {})
        w_honor = float(weights.get("honor_weight", 40.0))
        w_cons = float(weights.get("conscientiousness_weight", 25.0))
        w_piety = float(weights.get("piety_weight", 20.0))
        w_crime = float(weights.get("crime_propensity_reduction_weight", 35.0))
        exp_urgency = float(weights.get("urgency_power_exponent", 2.0))

        p = getattr(npc, "personality", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}
        v = getattr(npc, "vices", {}) or {}

        honor = float(sp.get("moral_values", {}).get("honor", 0.5))
        cons = float(p.get("conscientiousness", 0.5))
        piety = float(sp.get("reputation_facets", {}).get("moral_piety", 50.0)) / 100.0
        crime_prop = float(v.get("crime_propensity", 0.0)) / 100.0

        base_res = (honor * w_honor) + (cons * w_cons) + (piety * w_piety) - (crime_prop * w_crime)
        # Scaled by action severity
        severity_ratio = max(0.1, action_base_moral_cost / 35.0)
        base_res = max(0.0, base_res * severity_ratio)

        # Normalized urgency factor
        norm_urgency = max(1.0, float(urgency))
        denominator = norm_urgency ** exp_urgency
        effective_resistance = base_res / denominator

        return round(max(0.0, effective_resistance), 2)

    # -------------------------------------------------------------------------
    # 2. Multi-Tier Sustenance Problem Solving (Conventional -> Compensatory -> Transgressive)
    # -------------------------------------------------------------------------
    def evaluate_sustenance_pathways(
        self,
        npc: NPC,
        context: Any,
        current_tick: int
    ) -> List[ProblemSolvingPath]:
        """
        When hunger rises and primary food/money may be lacking, evaluate all possible paths:
        Tier 1: Inventory food, pantry stores, commercial purchase with cash.
        Tier 2: Borrow food from a trusting friend, forage scraps at meadow/orchard, emergency day labor.
        Tier 3: Petty shoplifting from bakery counter or mill grain sack.
        """
        cfg = self.get_volition_config()
        sust_cfg = cfg.get("sustenance_problem_solving", {})
        hunger = float(npc.needs.get("hunger", 0.0))
        wealth = float(getattr(npc, "wealth", 0.0))
        curr_loc = npc.location_id or "room_village_square"

        paths: List[ProblemSolvingPath] = []
        urgency = max(1.0, hunger / 25.0)

        # -----------------------------------------------------------------
        # TIER 1: CONVENTIONAL PATHWAYS
        # -----------------------------------------------------------------
        # 1a. Personal Inventory Food
        has_inv = any(any(k in getattr(i, "item_def_id", "").lower() for k in ("food", "bread", "ration", "stew", "pastry", "cider")) for i in getattr(npc, "inventory", []))
        if has_inv:
            paths.append(ProblemSolvingPath(
                path_id="CONVENTIONAL_INVENTORY",
                domain=ProblemSolvingDomain.SUSTENANCE,
                tier=VolitionTier.CONVENTIONAL,
                title="Eat from Personal Inventory",
                description="Consume packed provisions carried in personal inventory.",
                target_location_id=curr_loc,
                target_entity_id=npc.id,
                moral_cost=0.0,
                effective_viability=100.0,
                payload={"source_type": "INVENTORY"}
            ))

        # 1b. Household Pantry
        hh_eng = context.get_service("household_economy_engine") if hasattr(context, "get_service") else None
        if hh_eng:
            hh = hh_eng.get_household_for_npc(npc.id)
            if hh and getattr(hh, "pantry_food_rations", 0.0) >= 1.0:
                paths.append(ProblemSolvingPath(
                    path_id="CONVENTIONAL_PANTRY",
                    domain=ProblemSolvingDomain.SUSTENANCE,
                    tier=VolitionTier.CONVENTIONAL,
                    title="Eat from Domestic Pantry",
                    description=f"Dine on family hearth provisions stored at {hh.home_location_id}.",
                    target_location_id=hh.home_location_id,
                    target_entity_id=None,
                    moral_cost=0.0,
                    effective_viability=90.0,
                    payload={"source_type": "PANTRY"}
                ))

        # 1c. Commercial Market Purchase (if solvent)
        if wealth >= 1.20:
            paths.append(ProblemSolvingPath(
                path_id="CONVENTIONAL_MARKET_PURCHASE",
                domain=ProblemSolvingDomain.SUSTENANCE,
                tier=VolitionTier.CONVENTIONAL,
                title="Buy Food from Village Baker or Tavern",
                description="Purchase a freshly baked loaf or hot tavern stew using personal coin.",
                target_location_id="room_bakery" if "bakery" in curr_loc.lower() else "room_tavern",
                target_entity_id=None,
                moral_cost=0.0,
                effective_viability=80.0,
                payload={"source_type": "COMMERCIAL", "cost_gold": 1.20}
            ))

        # -----------------------------------------------------------------
        # TIER 2: COMPENSATORY PATHWAYS (Resourceful Adaptations)
        # -----------------------------------------------------------------
        # 2a. Borrowing / Sharing Food from a High-Trust Co-located Companion
        borrow_cfg = sust_cfg.get("borrowing", {})
        min_trust = float(borrow_cfg.get("min_relationship_trust", 40.0))
        min_aff = float(borrow_cfg.get("min_relationship_affection", 25.0))

        rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else None
        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None

        if hasattr(context, "npcs"):
            co_occupants = [
                n for n in context.npcs.values()
                if n.id != npc.id and n.location_id == curr_loc and getattr(n, "is_alive", True)
            ]
            for peer in co_occupants:
                peer_wealth = float(getattr(peer, "wealth", 0.0))
                peer_has_food = any("food" in getattr(i, "item_def_id", "").lower() for i in getattr(peer, "inventory", []))

                is_friend = False
                if rom_eng:
                    bond = rom_eng.get_or_create_bond(npc.id, peer.id, context=context)
                    if bond.trust >= min_trust or bond.romantic_affection >= min_aff:
                        is_friend = True

                if op_eng and not is_friend:
                    net_op = op_eng.get_net_opinion(npc.id, peer.id)
                    if net_op >= 35.0:
                        is_friend = True

                if is_friend and (peer_wealth >= 3.0 or peer_has_food):
                    paths.append(ProblemSolvingPath(
                        path_id="COMPENSATORY_BORROW_FOOD",
                        domain=ProblemSolvingDomain.SUSTENANCE,
                        tier=VolitionTier.COMPENSATORY,
                        title=f"Request Meal Share from {peer.name}",
                        description=f"Ask trusted companion {peer.name} to share bread or loan coins for food.",
                        target_location_id=curr_loc,
                        target_entity_id=peer.id,
                        moral_cost=5.0,
                        effective_viability=70.0 + (urgency * 5.0),
                        payload={"peer_id": peer.id, "peer_name": peer.name}
                    ))
                    break

        # 2b. Forage Edible Scraps / Orchard Fruit (Requires accessible outdoor perimeter)
        is_forageable = any(k in curr_loc.lower() for k in ("cottage", "square", "plaza", "field", "orchard", "woods", "meadow", "garden", "farm", "north", "south"))
        if is_forageable:
            forage_cfg = sust_cfg.get("foraging", {})
            forage_rooms = forage_cfg.get("foraging_rooms", ["room_cottage_north", "room_cottage_south", "room_village_square"])
            forage_loc = curr_loc if curr_loc in forage_rooms else forage_rooms[0]
            paths.append(ProblemSolvingPath(
                path_id="COMPENSATORY_FORAGE_SCRAPS",
                domain=ProblemSolvingDomain.SUSTENANCE,
                tier=VolitionTier.COMPENSATORY,
                title="Forage for Wild Fruit and Hearth Scraps",
                description=f"Search perimeter gardens and common hedgerows at {forage_loc} for fallen apples or wild berries.",
                target_location_id=forage_loc,
                target_entity_id=None,
                moral_cost=2.0,
                effective_viability=55.0 + (urgency * 4.0),
                payload={"forage_location": forage_loc}
            ))

        # 2c. Emergency Day Labor for Food (Requires accessible settlement circulation)
        can_labor = any(k in curr_loc.lower() for k in ("square", "plaza", "market", "tavern", "hall", "farm", "shop", "bakery", "cottage", "bedroom", "loft"))
        if can_labor:
            p = getattr(npc, "personality", {}) or {}
            cons = float(p.get("conscientiousness", 0.5))
            amb = float(getattr(npc, "mental_attributes", {}).get("ambition", 50.0)) / 100.0
            lab_pull = 35.0 + (cons * 25.0) + (amb * 15.0) + (urgency * 3.0)
            paths.append(ProblemSolvingPath(
                path_id="COMPENSATORY_DAY_LABOR",
                domain=ProblemSolvingDomain.SUSTENANCE,
                tier=VolitionTier.COMPENSATORY,
                title="Seek Emergency Casual Labor for Food Coin",
                description="Undertake immediate odd jobs or tavern dishwashing to earn meal money.",
                target_location_id="room_village_square",
                target_entity_id=None,
                moral_cost=0.0,
                effective_viability=round(lab_pull, 2),
                payload={"channel": "OFFICIAL"}
            ))

        # -----------------------------------------------------------------
        # TIER 3: TRANSGRESSIVE PATHWAYS (The Desperate Moral Frontier)
        # -----------------------------------------------------------------
        shop_cfg = sust_cfg.get("shoplifting", {})
        target_shops = shop_cfg.get("target_rooms", ["room_bakery", "room_shop", "room_windmill"])
        shop_target = curr_loc if curr_loc in target_shops else target_shops[0]

        # Evaluate moral resistance under current hunger urgency
        base_moral = float(shop_cfg.get("moral_cost", 35.0))
        effective_res = self.calculate_effective_moral_resistance(npc, urgency, action_base_moral_cost=base_moral)
        v = getattr(npc, "vices", {}) or {}
        crime_prop = float(v.get("crime_propensity", 0.0)) / 100.0
        base_pull = (hunger * 0.95) + (crime_prop * 20.0)
        viability = base_pull - effective_res

        can_reach_shop = curr_loc in target_shops or any(k in curr_loc.lower() for k in ("bakery", "shop", "windmill", "market", "square", "plaza", "tavern"))
        if can_reach_shop and viability > 0.0 and hunger >= float(sust_cfg.get("emergency_hunger_threshold", 65.0)):
            paths.append(ProblemSolvingPath(
                path_id="TRANSGRESSIVE_PETTY_SHOPLIFTING",
                domain=ProblemSolvingDomain.SUSTENANCE,
                tier=VolitionTier.TRANSGRESSIVE,
                title=f"Snatch Food from Counter at {shop_target}",
                description=f"Desperation drives opportunistically seizing bread or flour sacks from {shop_target}.",
                target_location_id=shop_target,
                target_entity_id=None,
                moral_cost=base_moral,
                effective_viability=round(viability, 2),
                payload={"shop_room": shop_target, "guilt_spike": float(shop_cfg.get("guilt_spike", 30.0))}
            ))

        # Sort by effective viability
        paths.sort(key=lambda p: p.effective_viability, reverse=True)
        return paths

    def execute_sustenance_problem_solving(
        self,
        npc: NPC,
        context: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """Executes the most viable sustenance problem-solving path for a hungry NPC."""
        paths = self.evaluate_sustenance_pathways(npc, context, current_tick)
        if not paths:
            return {"success": False, "reason": "No viable sustenance pathways discovered."}

        chosen = paths[0]
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        if chosen.tier == VolitionTier.CONVENTIONAL:
            # Resolved through standard conventional food acquisition
            return {"success": True, "path": chosen.to_dict(), "action": chosen.path_id}

        elif chosen.path_id == "COMPENSATORY_BORROW_FOOD":
            peer_id = chosen.payload.get("peer_id")
            peer = context.npcs.get(peer_id) if peer_id and hasattr(context, "npcs") else None
            if peer:
                npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 35.0)
                npc.adjust_feeling("contentment", 10.0)
                npc.adjust_feeling("tenderness", 12.0)
                peer.adjust_feeling("pride", 8.0) # Charitable pride

                npc.record_biographical_entry(
                    current_tick, time_iso, "FOOD_BORROWED",
                    f"In need of bread, approached trusted friend {peer.name} who generously shared their provisions.",
                    {"benefactor_id": peer.id}
                )
                peer.record_biographical_entry(
                    current_tick, time_iso, "ALMS_EXTENDED",
                    f"Shared domestic food provisions with hungry neighbor {npc.name}.",
                    {"recipient_id": npc.id}
                )
                self.total_food_borrowing_events += 1
                self.total_compensatory_actions += 1
                return {"success": True, "path": chosen.to_dict(), "action": "BORROW_FOOD_COMPANION"}

        elif chosen.path_id == "COMPENSATORY_FORAGE_SCRAPS":
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 25.0)
            npc.needs["energy"] = max(0.0, npc.needs.get("energy", 100.0) - 8.0)
            npc.adjust_feeling("contentment", 4.0)

            forage_loc = chosen.payload.get("forage_location", npc.location_id)
            npc.record_biographical_entry(
                current_tick, time_iso, "FORAGED_PROVISIONS",
                f"Foraged through perimeter hedgerows and orchard grounds at {forage_loc}, finding edible wild fruit.",
                {"location_id": forage_loc}
            )
            self.total_foraging_events += 1
            self.total_compensatory_actions += 1
            return {"success": True, "path": chosen.to_dict(), "action": "FORAGE_PROVISIONS"}

        elif chosen.path_id == "COMPENSATORY_DAY_LABOR":
            npc.current_action = "DAY_LABOR_FOR_BREAD"
            npc.record_biographical_entry(
                current_tick, time_iso, "EMERGENCY_DAY_LABOR",
                "Sought emergency casual labor in the village to earn money for sustenance."
            )
            self.total_compensatory_actions += 1
            return {"success": True, "path": chosen.to_dict(), "action": "DAY_LABOR_FOR_BREAD"}

        elif chosen.path_id == "TRANSGRESSIVE_PETTY_SHOPLIFTING":
            # Transgressive execution: petty shoplifting
            shop_room = chosen.payload.get("shop_room", "room_bakery")
            npc.location_id = shop_room

            # Check detection risk
            subterfuge = npc.get_skill("subterfuge") if hasattr(npc, "get_skill") else 10.0
            det_chance = max(0.05, 0.25 - (subterfuge * 0.005))
            caught = (context.random.random() < det_chance) if hasattr(context, "random") else False

            if caught:
                # Caught in the act!
                npc.adjust_feeling("stress", 35.0)
                npc.adjust_feeling("guilt", 25.0)
                npc.adjust_moral_erosion(2.0)
                npc.record_biographical_entry(
                    current_tick, time_iso, "SHOPLIFTING_CAUGHT",
                    f"Caught red-handed trying to snatch bread off the counter at {shop_room}; fled in disgrace!",
                    {"location_id": shop_room, "caught": True}
                )
                # Town alert
                info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
                if info_eng:
                    from src.society.information_networks import InformationChannelType
                    info_eng.publish_item(
                        channel=InformationChannelType.CRIME_AND_JUSTICE,
                        topic="PETTY_THEFT",
                        headline=f"Theft Attempt: {npc.name} caught stealing at {shop_room}",
                        content=f"Shopkeepers raised hue and cry after {npc.name} attempted to steal food.",
                        source_npc_id=None,
                        subject_npc_id=npc.id,
                        target_location_id=shop_room,
                        current_tick=current_tick,
                        context=context
                    )
                return {"success": False, "caught": True, "path": chosen.to_dict(), "action": "PETTY_SHOPLIFTING"}
            else:
                # Undetected: takes bread, hunger relieved, but carries psychological guilt
                npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 40.0)
                npc.adjust_feeling("guilt", chosen.payload.get("guilt_spike", 30.0))
                npc.adjust_feeling("stress", 18.0)
                npc.adjust_feeling("contentment", -5.0) # Lingering shame
                npc.adjust_moral_erosion(1.5)

                npc.record_biographical_entry(
                    current_tick, time_iso, "PETTY_THEFT_SUCCESSFUL",
                    f"Driven by gnawing hunger, quietly snatched bread off the counter at {shop_room} unseen.",
                    {"location_id": shop_room, "guilt_incurred": chosen.payload.get("guilt_spike", 30.0)}
                )

                # Record forensic clue in room
                ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
                if ep_eng:
                    ep_eng.record_crime_forensic_atoms(
                        perpetrator=npc,
                        victim=None,
                        crime_type="Petty Shoplifting",
                        location_id=shop_room,
                        context=context,
                        current_tick=current_tick
                    )

                self.total_shoplifting_events += 1
                self.total_transgressive_actions += 1
                return {"success": True, "caught": False, "path": chosen.to_dict(), "action": "PETTY_SHOPLIFTING"}

        return {"success": False, "reason": "Unhandled pathway."}

    # -------------------------------------------------------------------------
    # 3. Multi-Tier Courtship & Seclusion Problem Solving
    # -------------------------------------------------------------------------
    def evaluate_courtship_seclusion_pathways(
        self,
        actor: NPC,
        partner: NPC,
        context: Any,
        current_tick: int
    ) -> List[ProblemSolvingPath]:
        """
        When consensual lovers desire intimacy, evaluate where it can occur:
        Tier 1: Private owned bedroom (actor or partner's home bedroom).
        Tier 2: Rented inn room (tavern loft for 0.50g), or secluded unowned spot (farmhouse loft, meadow).
        Tier 3: Transgressive indoor trespassing (sneaking into an empty workshop/rectory after hours).
        """
        cfg = self.get_volition_config()
        court_cfg = cfg.get("courtship_problem_solving", {})
        sec_rooms = court_cfg.get("seclusion_rooms", {})

        paths: List[ProblemSolvingPath] = []
        passion = (float(actor.get_feeling("passion")) + float(partner.get_feeling("passion"))) / 2.0
        tension = (float(getattr(actor, "unmet_intimacy_tension", 0.0)) + float(getattr(partner, "unmet_intimacy_tension", 0.0))) / 2.0
        urgency = max(1.0, (passion + tension) / 45.0)

        # -----------------------------------------------------------------
        # TIER 1: OWNED HOME BEDROOM
        # -----------------------------------------------------------------
        actor_home = getattr(actor, "home_location_id", None)
        partner_home = getattr(partner, "home_location_id", None)
        priv_keywords = ("bedroom", "quarters", "loft", "chambers", "cottage")

        owned_room = None
        for cand in (actor_home, partner_home):
            if cand and any(k in cand.lower() for k in priv_keywords):
                # Verify it's not a public shared dormitory with excess occupants
                owned_room = cand
                break

        if owned_room:
            paths.append(ProblemSolvingPath(
                path_id="CONVENTIONAL_OWNED_BEDROOM",
                domain=ProblemSolvingDomain.COURTSHIP,
                tier=VolitionTier.CONVENTIONAL,
                title="Retire to Private Home Bedchamber",
                description=f"Retire to peaceful private quarters at {owned_room}.",
                target_location_id=owned_room,
                target_entity_id=partner.id,
                moral_cost=0.0,
                effective_viability=95.0,
                payload={"destination": owned_room}
            ))

        # -----------------------------------------------------------------
        # TIER 2: COMPENSATORY SECLUSION (Room Rental or Secluded Spot)
        # -----------------------------------------------------------------
        rental_fee = float(court_cfg.get("rental_fee_gold", 0.50))
        has_rental_coin = (getattr(actor, "wealth", 0.0) >= rental_fee or getattr(partner, "wealth", 0.0) >= rental_fee)
        rental_rooms = sec_rooms.get("RENTAL", ["room_tavern_bedroom"])

        if has_rental_coin and rental_rooms:
            paths.append(ProblemSolvingPath(
                path_id="COMPENSATORY_RENTED_ROOM",
                domain=ProblemSolvingDomain.COURTSHIP,
                tier=VolitionTier.COMPENSATORY,
                title=f"Rent Private Loft at {rental_rooms[0]}",
                description=f"Pay modest rental fee ({rental_fee:.2f}g) to tavern keeper for private overnight quarters.",
                target_location_id=rental_rooms[0],
                target_entity_id=partner.id,
                moral_cost=2.0,
                effective_viability=85.0,
                payload={"destination": rental_rooms[0], "fee_gold": rental_fee}
            ))

        # Secluded unowned nooks (Haylofts, secluded brook, storage loft)
        secluded_rooms = sec_rooms.get("SECLUDED", ["room_farmhouse_loft", "room_cottage_bedroom_north"])
        if secluded_rooms:
            paths.append(ProblemSolvingPath(
                path_id="COMPENSATORY_SECLUDED_SPOT",
                domain=ProblemSolvingDomain.COURTSHIP,
                tier=VolitionTier.COMPENSATORY,
                title=f"Retreat to Secluded Nook at {secluded_rooms[0]}",
                description=f"Seek unmonitored clandestine seclusion in quiet hayloft or meadow at {secluded_rooms[0]}.",
                target_location_id=secluded_rooms[0],
                target_entity_id=partner.id,
                moral_cost=5.0,
                effective_viability=75.0 + (urgency * 4.0),
                payload={"destination": secluded_rooms[0], "clandestine_thrill": float(court_cfg.get("clandestine_passion_bonus", 10.0))}
            ))

        # -----------------------------------------------------------------
        # TIER 3: TRANSGRESSIVE SECLUSION (Trespassing Indoors)
        # -----------------------------------------------------------------
        trespass_rooms = sec_rooms.get("TRESPASSING", ["room_blacksmith", "room_carpenter", "room_windmill", "room_bakery"])
        trespass_target = trespass_rooms[0] if trespass_rooms else "room_carpenter"

        base_moral = float(court_cfg.get("trespass_moral_cost", 30.0))
        eff_res_actor = self.calculate_effective_moral_resistance(actor, urgency, action_base_moral_cost=base_moral)
        eff_res_partner = self.calculate_effective_moral_resistance(partner, urgency, action_base_moral_cost=base_moral)
        avg_res = (eff_res_actor + eff_res_partner) / 2.0

        viability = (passion * 0.85) - avg_res
        if viability > 0.0:
            paths.append(ProblemSolvingPath(
                path_id="TRANSGRESSIVE_TRESPASSING_INDOORS",
                domain=ProblemSolvingDomain.COURTSHIP,
                tier=VolitionTier.TRANSGRESSIVE,
                title=f"Slip Clandestinely into Workshop at {trespass_target}",
                description=f"Overwhelming romantic longing drives lovers to slip into an empty workshop at {trespass_target} after hours.",
                target_location_id=trespass_target,
                target_entity_id=partner.id,
                moral_cost=base_moral,
                effective_viability=round(viability, 2),
                payload={
                    "destination": trespass_target,
                    "guilt_spike": float(court_cfg.get("trespass_guilt_spike", 20.0)),
                    "stress_spike": float(court_cfg.get("trespass_stress_spike", 15.0))
                }
            ))

        paths.sort(key=lambda p: p.effective_viability, reverse=True)
        return paths

    # -------------------------------------------------------------------------
    # 4. Aspirational Skill Bridging for Careers
    # -------------------------------------------------------------------------
    def register_career_aspiration(
        self,
        npc: NPC,
        target_occupation: str,
        required_skill: str,
        required_level: float,
        current_level: float,
        current_tick: int
    ) -> AspirationalCareerDeficit:
        """Registers a deficit when an NPC aspires to a career but lacks certification level."""
        deficit = max(0.0, required_level - current_level)
        p = getattr(npc, "personality", {}) or {}
        amb = float(getattr(npc, "mental_attributes", {}).get("ambition", 50.0))
        cons = float(p.get("conscientiousness", 0.5))

        priority = round(1.0 + (amb / 50.0) + cons, 2)
        record = AspirationalCareerDeficit(
            npc_id=npc.id,
            target_occupation=target_occupation,
            required_skill=required_skill,
            required_level=required_level,
            current_level=current_level,
            deficit=deficit,
            priority_score=priority,
            created_tick=current_tick
        )
        self.aspirations[npc.id] = record
        return record

    def advance_vocational_skill_bridging(
        self,
        npc: NPC,
        method: str, # "STUDY", "OBSERVE", "PRACTICE"
        context: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """
        Advances an agent's skill towards qualifying for an aspirational career:
        - STUDY: reading trade manuals / tomes.
        - OBSERVE: watching a master artisan at work in the workshop.
        - PRACTICE: hands-on solitary practice at community anvil or workbench.
        """
        aspiration = self.aspirations.get(npc.id)
        if not aspiration:
            return {"success": False, "reason": "No active career aspiration."}

        cfg = self.get_volition_config()
        voc_cfg = cfg.get("vocational_aspirations", {})

        gain = 0.5
        if method == "OBSERVE":
            gain = float(voc_cfg.get("observation_skill_gain_per_hour", 1.25))
        elif method == "PRACTICE":
            gain = float(voc_cfg.get("practice_skill_gain_per_hour", 0.90))
        else: # STUDY
            gain = float(voc_cfg.get("study_skill_gain_per_hour", 0.75))

        skill_name = aspiration.required_skill
        cur_skill = npc.get_skill(skill_name) if hasattr(npc, "get_skill") else 10.0
        new_skill = min(100.0, cur_skill + gain)
        if hasattr(npc, "skills"):
            npc.skills[skill_name] = round(new_skill, 2)

        aspiration.current_level = new_skill
        aspiration.deficit = max(0.0, aspiration.required_level - new_skill)

        npc.needs["energy"] = max(0.0, npc.needs.get("energy", 100.0) - float(voc_cfg.get("energy_drain_study", 10.0)))
        npc.adjust_feeling("contentment", 6.0)
        npc.adjust_feeling("pride", 5.0)

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        npc.record_biographical_entry(
            current_tick, time_iso, "VOCATIONAL_SKILL_STUDY",
            f"Dedicated focused time to {method.lower()} for {skill_name} (progressed to {new_skill:.1f}/{aspiration.required_level:.1f}).",
            {"skill": skill_name, "level": new_skill, "target_role": aspiration.target_occupation}
        )

        qualified = (new_skill >= aspiration.required_level)
        if qualified:
            del self.aspirations[npc.id]
            npc.record_biographical_entry(
                current_tick, time_iso, "CAREER_QUALIFICATION_ACHIEVED",
                f"Successfully achieved required skill competence ({new_skill:.1f}) to qualify as {aspiration.target_occupation}!",
                {"target_role": aspiration.target_occupation}
            )

        self.total_aspirational_study_hours += 1
        return {
            "success": True,
            "skill": skill_name,
            "new_level": round(new_skill, 2),
            "deficit_remaining": round(aspiration.deficit if not qualified else 0.0, 2),
            "qualified": qualified
        }

    # -------------------------------------------------------------------------
    # 5. Closed-Loop Guilt & Spiritual Aftermath
    # -------------------------------------------------------------------------
    def evaluate_guilt_remedy(
        self,
        npc: NPC,
        context: Any,
        current_tick: int
    ) -> Optional[Dict[str, Any]]:
        """
        When guilt exceeds threshold (> 20.0), drives the NPC towards confession
        or restitution rather than ignoring psychological aftermath.
        """
        guilt = float(npc.get_feeling("guilt")) if hasattr(npc, "get_feeling") else 0.0
        if guilt < 20.0:
            return None

        # Look for Chapel & Priest
        chapel_rooms = context.find_rooms_by_keyword("chapel") if hasattr(context, "find_rooms_by_keyword") else []
        chapel_room = chapel_rooms[0] if chapel_rooms else "room_chapel"
        priest = context.find_npc_by_role(["priest"]) if hasattr(context, "find_npc_by_role") else None

        return {
            "urgency": guilt / 20.0,
            "recommended_action": "SPIRITUAL_CONFESSION",
            "destination": chapel_room,
            "confessor_id": priest.id if priest else None
        }

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "total_compensatory_actions": self.total_compensatory_actions,
            "total_transgressive_actions": self.total_transgressive_actions,
            "total_aspirational_study_hours": self.total_aspirational_study_hours,
            "total_shoplifting_events": self.total_shoplifting_events,
            "total_food_borrowing_events": self.total_food_borrowing_events,
            "total_foraging_events": self.total_foraging_events,
            "total_trespass_trysts": self.total_trespass_trysts,
            "active_aspirations_count": len(self.aspirations)
        }
