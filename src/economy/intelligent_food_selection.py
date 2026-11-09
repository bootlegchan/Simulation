"""
Intelligent Food & Vendor Selection Engine.
Evaluates dining options across inventory, domestic pantry, and settlement food vendors
using multi-attribute utility (travel friction, price-to-wealth, culinary palate match,
freshness/quality, and kinship/trust) with 100% declarative vocational offerings.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple

from src.entities.npc import NPC
from src.entities.item import ItemInstance

class FoodSourceType(Enum):
    INVENTORY_ITEM = "INVENTORY_ITEM"
    HOUSEHOLD_PANTRY = "HOUSEHOLD_PANTRY"
    COMMERCIAL_BAKERY = "COMMERCIAL_BAKERY"
    TAVERN_HOSPITALITY = "TAVERN_HOSPITALITY"
    MARKET_STALL = "MARKET_STALL"
    DIRECT_PRODUCER = "DIRECT_PRODUCER"
    MUNICIPAL_GRANARY = "MUNICIPAL_GRANARY"

class CulinaryPalatePreference(Enum):
    WHOLESOME_HEARTH_BREAD = "WHOLESOME_HEARTH_BREAD"
    ROASTED_MEAT_AND_ALE = "ROASTED_MEAT_AND_ALE"
    RUSTIC_FARM_STEW = "RUSTIC_FARM_STEW"
    SWEET_HONEY_PASTRY = "SWEET_HONEY_PASTRY"
    MONASTIC_PLAIN_LOAF = "MONASTIC_PLAIN_LOAF"
    FRESH_CIDER_AND_FRUIT = "FRESH_CIDER_AND_FRUIT"

@dataclass
class DiningCandidate:
    source_type: FoodSourceType
    source_name: str
    location_id: str
    vendor_id: Optional[str]
    item_def_id: str
    price_gold: float
    quality_score: float
    specialty_palate: CulinaryPalatePreference
    estimated_distance_hops: int
    relationship_score: float = 0.0
    utility_score: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "location_id": self.location_id,
            "vendor_id": self.vendor_id,
            "item_def_id": self.item_def_id,
            "price_gold": self.price_gold,
            "quality_score": round(self.quality_score, 1),
            "specialty_palate": self.specialty_palate.value,
            "estimated_distance_hops": self.estimated_distance_hops,
            "relationship_score": round(self.relationship_score, 1),
            "utility_score": round(self.utility_score, 2),
            "score_breakdown": {k: round(v, 2) for k, v in self.score_breakdown.items()}
        }

class IntelligentFoodSelector:
    """Evaluates dining options across inventory, pantry, and town vendors with multi-attribute utility."""

    @staticmethod
    def infer_palate_preference(npc: NPC) -> CulinaryPalatePreference:
        """Dynamically resolves palate preference from character profile or vocational declaration."""
        # 1. Declared personal taste preference in character profile
        cog = getattr(npc, "cognition", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}
        declared = cog.get("taste_preference") or sp.get("taste_preference")
        if declared:
            for p in CulinaryPalatePreference:
                if p.value == declared or declared in p.value:
                    return p

        # 2. Declarative vocational palate from occupations.json
        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()
        pal_str = occ_reg.get_palate_preference(getattr(npc, "occupation", ""))
        for p in CulinaryPalatePreference:
            if p.value == pal_str or pal_str in p.value:
                return p

        return CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD

    @classmethod
    def evaluate_distance_hops(cls, start_room: str, target_room: str, context: Any) -> int:
        if not start_room or not target_room or start_room == target_room:
            return 0
        graph = getattr(context, "spatial_graph", None)
        if graph and hasattr(graph, "find_shortest_path"):
            path = graph.find_shortest_path(start_room, target_room)
            if path:
                return max(0, len(path) - 1)
        return 2

    @classmethod
    def evaluate_vendor_relationship(cls, customer: NPC, vendor: NPC, context: Any) -> float:
        score = 50.0
        if customer.id == vendor.id:
            return 100.0
        if customer.social_profile.get("spouse_id") == vendor.id or customer.social_profile.get("partner_id") == vendor.id:
            score += 35.0
        elif getattr(customer, "household_id", None) and customer.household_id == getattr(vendor, "household_id", None):
            score += 25.0

        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        if op_eng and hasattr(op_eng, "get_net_opinion"):
            score += max(-40.0, min(40.0, op_eng.get_net_opinion(customer.id, vendor.id) * 0.5))

        grudge_eng = context.get_service("memory_grudge_engine") if hasattr(context, "get_service") else None
        if grudge_eng and hasattr(grudge_eng, "has_grudge_against"):
            if grudge_eng.has_grudge_against(customer.id, vendor.id):
                score -= 45.0
        return max(0.0, min(100.0, score))

    @classmethod
    def assemble_candidates(cls, diner: NPC, context: Any, emergency_hunger: bool = False) -> List[DiningCandidate]:
        candidates: List[DiningCandidate] = []
        central_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
        curr_loc = diner.location_id or central_plaza

        # 1. Personal Inventory Food
        for item in diner.inventory:
            i_def = getattr(item, "item_def_id", "").lower()
            if any(k in i_def for k in ("food", "bread", "cider", "apple", "stew", "meat", "pastry")):
                candidates.append(DiningCandidate(
                    source_type=FoodSourceType.INVENTORY_ITEM,
                    source_name=f"Personal Inventory ({item.item_def_id})",
                    location_id=curr_loc,
                    vendor_id=diner.id,
                    item_def_id=item.item_def_id,
                    price_gold=0.0,
                    quality_score=getattr(item, "quality", 1.0) * 30.0 + getattr(item, "freshness", 100.0) * 0.4,
                    specialty_palate=CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD,
                    estimated_distance_hops=0,
                    relationship_score=100.0
                ))

        # 2. Household Pantry
        hh_eng = context.get_service("household_economy_engine") if hasattr(context, "get_service") else None
        home_loc = diner.home_location_id or curr_loc
        if hh_eng:
            hh = hh_eng.get_household_for_npc(diner.id)
            if hh and getattr(hh, "pantry_food_rations", 0) >= 1.0:
                dist = cls.evaluate_distance_hops(curr_loc, home_loc, context)
                candidates.append(DiningCandidate(
                    source_type=FoodSourceType.HOUSEHOLD_PANTRY,
                    source_name=f"Household Pantry Stores ({hh.household_id})",
                    location_id=home_loc,
                    vendor_id=None,
                    item_def_id="hearth_pantry_ration",
                    price_gold=0.0,
                    quality_score=60.0 + (15.0 if "hearth" in curr_loc.lower() else 0.0),
                    specialty_palate=CulinaryPalatePreference.RUSTIC_FARM_STEW,
                    estimated_distance_hops=dist,
                    relationship_score=95.0
                ))

        # 3. Commercial Vendors (Evaluated dynamically via OccupationRegistry offerings)
        sc_eng = context.get_service("supply_chain_engine") if hasattr(context, "get_service") else None
        from src.configuration.settings import SettingsRegistry
        cul_cfg = SettingsRegistry.get_instance().get("culinary_economy")
        def_prices = cul_cfg.get("default_commodity_prices", {})

        if sc_eng and hasattr(sc_eng, "get_stock_level"):
            bread_p = sc_eng.calculate_market_price("food_bread")
        else:
            bread_p = float(def_prices.get("food_bread", 1.20))

        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()

        for npc in context.npcs.values():
            if npc.id == diner.id or not getattr(npc, "is_alive", True):
                continue

            offering = occ_reg.get_food_offering(getattr(npc, "occupation", ""))
            if offering:
                work_loc = npc.work_location_id or npc.location_id or central_plaza
                s_type_str = offering.get("source_type", "DIRECT_PRODUCER")
                v_type = FoodSourceType(s_type_str) if s_type_str in FoodSourceType._value2member_map_ else FoodSourceType.DIRECT_PRODUCER
                item_def = offering.get("item_def_id", "food_bread")
                price = bread_p * float(offering.get("price_multiplier", 1.0))
                skill_name = offering.get("skill_eval", "crafting")
                base_qual = float(offering.get("quality_baseline", 60.0)) + (npc.get_skill(skill_name) * 0.20)
                pal_str = offering.get("palate", "WHOLESOME_HEARTH_BREAD")
                v_palate = CulinaryPalatePreference(pal_str) if pal_str in CulinaryPalatePreference._value2member_map_ else CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD

                dist = cls.evaluate_distance_hops(curr_loc, work_loc, context)
                rel = cls.evaluate_vendor_relationship(diner, npc, context)
                candidates.append(DiningCandidate(
                    source_type=v_type,
                    source_name=f"{npc.name}'s {getattr(npc, 'occupation', 'Goods')}",
                    location_id=work_loc,
                    vendor_id=npc.id,
                    item_def_id=item_def,
                    price_gold=round(price, 2),
                    quality_score=round(base_qual, 1),
                    specialty_palate=v_palate,
                    estimated_distance_hops=dist,
                    relationship_score=rel
                ))

        # 4. Municipal Granary Buffer
        granary = context.get_service("granary_engine") if hasattr(context, "get_service") else None
        if granary and getattr(granary, "stored_bread_loaves", 0) > 0:
            granary_room = getattr(granary, "location_id", central_plaza) or central_plaza
            dist = cls.evaluate_distance_hops(curr_loc, granary_room, context)
            candidates.append(DiningCandidate(
                source_type=FoodSourceType.MUNICIPAL_GRANARY,
                source_name="Municipal Granary Buffer",
                location_id=granary_room,
                vendor_id=None,
                item_def_id="granary_relief_loaf",
                price_gold=0.0,
                quality_score=40.0,
                specialty_palate=CulinaryPalatePreference.MONASTIC_PLAIN_LOAF,
                estimated_distance_hops=dist,
                relationship_score=50.0
            ))

        return candidates

    @classmethod
    def evaluate_and_rank_candidates(
        cls,
        diner: NPC,
        candidates: List[DiningCandidate],
        emergency_hunger: bool = False
    ) -> List[DiningCandidate]:
        from src.configuration.settings import SettingsRegistry
        cul_cfg = SettingsRegistry.get_instance().get("culinary_economy")
        w_default = cul_cfg.get("multi_attribute_weights", {}).get("default", {})
        w_emerg = cul_cfg.get("multi_attribute_weights", {}).get("emergency", {})
        scoring_mods = cul_cfg.get("scoring_modifiers", {})

        palate = cls.infer_palate_preference(diner)
        wealth = float(getattr(diner, "wealth", 0.0))
        hunger = float(diner.needs.get("hunger", 0.0))

        is_emerg = emergency_hunger or hunger >= 80.0
        w_dist = float(w_emerg.get("distance", 40.0) if is_emerg else w_default.get("distance", 25.0))
        if wealth < 10.0:
            w_cost = float(w_default.get("affordability_poor", 45.0))
        elif wealth < 40.0:
            w_cost = float(w_default.get("affordability_modest", 20.0))
        else:
            w_cost = float(w_default.get("affordability_wealthy", 10.0))
        w_taste = float(w_emerg.get("taste", 15.0) if emergency_hunger else w_default.get("taste", 25.0))
        w_qual = float(w_emerg.get("quality", 10.0) if emergency_hunger else w_default.get("quality", 20.0))
        w_rel = float(w_emerg.get("relationship", 10.0) if emergency_hunger else w_default.get("relationship", 15.0))

        unaffordable_penalty = float(scoring_mods.get("unaffordable_penalty", -9999.0))
        granary_civic_shame = float(scoring_mods.get("granary_civic_shame", -30.0))
        pal_exact_mult = float(scoring_mods.get("palate_exact_multiplier", 1.0))
        pal_rel_mult = float(scoring_mods.get("palate_related_multiplier", 0.70))
        pal_mis_mult = float(scoring_mods.get("palate_mismatch_multiplier", 0.30))
        dist_decay = float(scoring_mods.get("distance_hop_decay", 0.45))
        cost_mult = float(scoring_mods.get("cost_ratio_multiplier", 0.80))

        for cand in candidates:
            breakdown = {}
            if cand.price_gold > wealth:
                cand.utility_score = unaffordable_penalty
                cand.score_breakdown = {"unaffordable": unaffordable_penalty}
                continue

            cost_ratio = cand.price_gold / max(1.0, wealth)
            u_cost = max(0.0, 1.0 - min(1.0, cost_ratio * cost_mult)) * w_cost
            breakdown["affordability"] = u_cost

            hops = cand.estimated_distance_hops
            u_dist = (1.0 / (1.0 + (hops * dist_decay))) * w_dist
            breakdown["proximity"] = u_dist

            if cand.specialty_palate == palate:
                u_taste = w_taste * pal_exact_mult
            elif (palate in (CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD, CulinaryPalatePreference.RUSTIC_FARM_STEW)
                  and cand.specialty_palate in (CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD, CulinaryPalatePreference.RUSTIC_FARM_STEW)):
                u_taste = w_taste * pal_rel_mult
            else:
                u_taste = w_taste * pal_mis_mult
            breakdown["taste_match"] = u_taste

            u_qual = (cand.quality_score / 100.0) * w_qual
            breakdown["quality"] = u_qual

            u_rel = (cand.relationship_score / 100.0) * w_rel
            breakdown["relationship"] = u_rel

            if cand.source_type == FoodSourceType.MUNICIPAL_GRANARY and wealth >= 5.0:
                breakdown["civic_shame"] = granary_civic_shame

            cand.utility_score = sum(breakdown.values())
            cand.score_breakdown = breakdown

        candidates.sort(key=lambda c: c.utility_score, reverse=True)
        return candidates

    @classmethod
    def select_best_option(
        cls,
        diner: NPC,
        context: Any,
        emergency_hunger: bool = False
    ) -> Optional[DiningCandidate]:
        candidates = cls.assemble_candidates(diner, context, emergency_hunger)
        ranked = cls.evaluate_and_rank_candidates(diner, candidates, emergency_hunger)
        valid = [c for c in ranked if c.utility_score > -500.0]
        return valid[0] if valid else None
