"""
Domestic Household Economy, Flexible Cohabitation & Overcrowding Dynamics.
Operates 100% on declarative policies from data/settings/desire_hierarchy.json.
Supports:
1. MARITAL_COMMUNION: Married couples who agreed to shared wealth pooling.
2. COHABITING_PARTNERS: Romantic couples living together with separate individual wallets.
3. COLLECTIVE_LODGERS: Non-romantic roommates sharing living space due to affordability,
   maintaining strictly separate wallets and private accounts.
4. Overcrowding comfort penalties and sleep/rest efficiency drag.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.configuration.settings import SettingsRegistry


class HouseholdType(str, Enum):
    MARITAL_COMMUNION = "MARITAL_COMMUNION"         # Married couple with shared wealth pooling
    COHABITING_PARTNERS = "COHABITING_PARTNERS"     # Romantic partners living together, separate wallets
    COLLECTIVE_LODGERS = "COLLECTIVE_LODGERS"       # Non-romantic roommates splitting dwelling, separate wallets
    SINGLE_DWELLING = "SINGLE_DWELLING"             # Sole occupant


@dataclass
class Household:
    household_id: str
    home_location_id: str
    household_type: HouseholdType = HouseholdType.SINGLE_DWELLING
    member_ids: List[str] = field(default_factory=list)
    shares_wealth: bool = False
    shared_treasury_gold: float = 0.0
    pantry_food_rations: float = 10.0
    standard_capacity: int = 2
    overcrowding_drag: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "household_id": self.household_id,
            "home_location_id": self.home_location_id,
            "household_type": self.household_type.value if hasattr(self.household_type, "value") else str(self.household_type),
            "member_ids": list(self.member_ids),
            "shares_wealth": self.shares_wealth,
            "shared_treasury_gold": round(self.shared_treasury_gold, 2),
            "pantry_food_rations": round(self.pantry_food_rations, 2),
            "standard_capacity": self.standard_capacity,
            "overcrowding_drag": round(self.overcrowding_drag, 2)
        }


class HouseholdEconomyEngine:
    """
    Central Household and Cohabitation Engine.
    Discovers households based on dwelling occupancy, assigns appropriate cohabitation models
    (marital communion vs separate wallets for roommates/partners), tracks domestic food pantries,
    and calculates overcrowding comfort penalties.
    """
    _instance: Optional["HouseholdEconomyEngine"] = None

    @classmethod
    def get_instance(cls) -> "HouseholdEconomyEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.households: Dict[str, Household] = {}

    def clear(self) -> None:
        self.households.clear()

    def get_household_for_npc(self, npc_id: str) -> Optional[Household]:
        for h in self.households.values():
            if npc_id in h.member_ids:
                return h
        return None

    def get_household_by_id(self, hid: str) -> Optional[Household]:
        return self.households.get(hid)

    def consume_pantry_meal(self, npc: Any, current_tick: int = 0) -> bool:
        """Any cohabitant can eat from the shared domestic pantry."""
        h = self.get_household_for_npc(npc.id)
        if h and h.pantry_food_rations >= 1.0:
            h.pantry_food_rations = max(0.0, round(h.pantry_food_rations - 1.0, 2))
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 35.0)
            return True
        return False

    def restock_pantry(self, npc: Any, rations: float = 5.0) -> bool:
        h = self.get_household_for_npc(npc.id)
        if h:
            h.pantry_food_rations = round(h.pantry_food_rations + rations, 2)
            return True
        return False

    def deposit_income_share(self, npc: Any, earned_gold: float) -> None:
        """
        Wealth pooling only occurs if the household is MARITAL_COMMUNION
        and members agreed to share finances. Lodgers and unmarried couples keep 100% separate wallets!
        """
        h = self.get_household_for_npc(npc.id)
        if h and h.shares_wealth and earned_gold > 0:
            share = round(earned_gold * 0.25, 2)
            if getattr(npc, "wealth", 0.0) >= share:
                npc.wealth = round(npc.wealth - share, 2)
                h.shared_treasury_gold = round(h.shared_treasury_gold + share, 2)

    def draw_from_shared_treasury(self, npc: Any, amount: float) -> float:
        """Only communion members can draw from shared treasury."""
        h = self.get_household_for_npc(npc.id)
        if h and h.shares_wealth and h.shared_treasury_gold > 0:
            drawn = min(h.shared_treasury_gold, amount)
            h.shared_treasury_gold = round(h.shared_treasury_gold - drawn, 2)
            npc.wealth = round(npc.wealth + drawn, 2)
            return drawn
        return 0.0

    def get_room_overcrowding_drag(self, room_id: str) -> float:
        """Calculates continuous overcrowding drag if dwelling occupants exceed capacity."""
        if not room_id:
            return 0.0
        cfg = SettingsRegistry.get_instance().get("desire_hierarchy").get("desire_hierarchy", {}).get("cohabitation_dynamics", {})
        std_cap = int(cfg.get("standard_room_capacity", 2))
        pen = float(cfg.get("overcrowding_penalty_per_excess_occupant", 0.25))
        max_drag = float(cfg.get("max_overcrowding_drag", 0.60))

        for h in self.households.values():
            if h.home_location_id == room_id:
                excess = max(0, len(h.member_ids) - h.standard_capacity)
                return min(max_drag, round(excess * pen, 2))
        return 0.0

    def auto_discover_households(self, npcs: Dict[str, Any]) -> None:
        """
        Discovers households from NPC dwelling locations:
        - Groups cohabitants by home_location_id.
        - Identifies married communion vs cohabiting partners vs non-romantic lodger roommates.
        - Enforces strict wealth separation for non-married cohabitants.
        """
        self.households.clear()
        cfg = SettingsRegistry.get_instance().get("desire_hierarchy").get("desire_hierarchy", {}).get("cohabitation_dynamics", {})
        std_cap = int(cfg.get("standard_room_capacity", 2))
        pen = float(cfg.get("overcrowding_penalty_per_excess_occupant", 0.25))
        max_drag = float(cfg.get("max_overcrowding_drag", 0.60))

        # Group NPCs by home_location_id
        home_groups: Dict[str, List[Any]] = {}
        for npc in npcs.values():
            home = getattr(npc, "home_location_id", None) or f"home_{npc.id}"
            home_groups.setdefault(home, []).append(npc)

        for home_loc, cohabitants in home_groups.items():
            hid = f"hh_{home_loc.replace('room_', '')}"
            member_ids = [m.id for m in cohabitants]
            num_members = len(cohabitants)

            # Capacity and overcrowding drag
            room_cap = 3 if "bedroom" in home_loc or "loft" in home_loc else std_cap
            excess = max(0, num_members - room_cap)
            drag = min(max_drag, round(excess * pen, 2))

            # Determine Household Type & Wealth Sharing Agreement
            hh_type = HouseholdType.SINGLE_DWELLING
            shares_wealth = False
            initial_vault = 0.0

            if num_members == 1:
                hh_type = HouseholdType.SINGLE_DWELLING
                shares_wealth = False
            elif num_members == 2:
                npc_a, npc_b = cohabitants[0], cohabitants[1]
                sp_a = getattr(npc_a, "social_profile", {}) or {}
                sp_b = getattr(npc_b, "social_profile", {}) or {}

                is_married = (sp_a.get("spouse_id") == npc_b.id and sp_b.get("spouse_id") == npc_a.id)
                is_partnered = (sp_a.get("partner_id") == npc_b.id or sp_b.get("partner_id") == npc_a.id)

                if is_married:
                    # Married couple with mutual agreement: marital communion
                    hh_type = HouseholdType.MARITAL_COMMUNION
                    shares_wealth = True
                    # Small initial shared household savings pooled from private wealth
                    initial_vault = 20.0
                elif is_partnered:
                    # Unmarried romantic couple cohabitating: separate wallets!
                    hh_type = HouseholdType.COHABITING_PARTNERS
                    shares_wealth = False
                else:
                    # Non-romantic roommates sharing living space
                    hh_type = HouseholdType.COLLECTIVE_LODGERS
                    shares_wealth = False
            else:
                # 3 or more occupants: check if family or collective lodgers
                has_married_pair = False
                for i in range(num_members):
                    for j in range(i + 1, num_members):
                        na, nb = cohabitants[i], cohabitants[j]
                        if getattr(na, "social_profile", {}).get("spouse_id") == nb.id:
                            has_married_pair = True
                            break

                if has_married_pair:
                    hh_type = HouseholdType.MARITAL_COMMUNION
                    shares_wealth = True
                    initial_vault = 20.0
                else:
                    # Non-romantic lodgers / apprentice cluster: strictly separate wallets!
                    hh_type = HouseholdType.COLLECTIVE_LODGERS
                    shares_wealth = False

            household = Household(
                household_id=hid,
                home_location_id=home_loc,
                household_type=hh_type,
                member_ids=member_ids,
                shares_wealth=shares_wealth,
                shared_treasury_gold=initial_vault,
                pantry_food_rations=12.0 if num_members > 1 else 6.0,
                standard_capacity=room_cap,
                overcrowding_drag=drag
            )
            self.households[hid] = household

            for npc in cohabitants:
                npc.household_id = hid
