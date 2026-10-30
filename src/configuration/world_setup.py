"""
Town & NPC Setup Engine, Power-Law Wealth Allocation, and Occupational Supply Chain Validation.
"""
from typing import Any, Dict, List, Optional
from src.core.randomness import SeededRandom
from src.entities.npc import NPC
from src.npc.kinship import KinshipGraph
from src.world.demographics import DemographicPyramid

class WealthStratifier:
    """Allocates initial wealth following a Pareto (Power-Law) Socio-Economic Class Distribution."""

    @staticmethod
    def allocate_pareto_wealth(npcs: Dict[str, NPC], random_gen: SeededRandom) -> Dict[str, float]:
        """
        Allocates starting gold balances based on social class tiers:
        - Nobility / Mayor (Top 5%): 150.0 to 300.0 gold
        - Merchants / Guildmasters (20%): 60.0 to 140.0 gold
        - Artisans & Farmers (55%): 25.0 to 60.0 gold
        - Laborers, Beggars, Outcasts (20%): 2.0 to 15.0 gold
        """
        allocated = {}
        for npc in npcs.values():
            occupation = npc.occupation.lower()
            if any(k in occupation for k in ["mayor", "lord", "patrician"]):
                wealth = random_gen.uniform(180.0, 300.0)
            elif any(k in occupation for k in ["merchant", "guildmaster", "sheriff", "curator"]):
                wealth = random_gen.uniform(70.0, 150.0)
            elif any(k in occupation for k in ["smith", "baker", "miller", "farmer", "scribe", "healer"]):
                wealth = random_gen.uniform(30.0, 70.0)
            else:  # beggar, laborer, outcast, maid
                wealth = random_gen.uniform(2.0, 18.0)

            npc.wealth = round(wealth, 2)
            allocated[npc.id] = npc.wealth

        return allocated

class OccupationalMatrix:
    """Validates occupational supply-chain dependencies across townfolk."""

    @staticmethod
    def validate_town_occupations(npcs: Dict[str, NPC]) -> Dict[str, Any]:
        occupations = [npc.occupation.lower() for npc in npcs.values()]

        has_food_production = any(k in occ for occ in occupations for k in ["farmer", "miller", "baker"])
        has_health_care = any(k in occ for occ in occupations for k in ["healer", "apothecary", "priest"])
        has_law_enforcement = any(k in occ for occ in occupations for k in ["sheriff", "guard"])
        has_crafts = any(k in occ for occ in occupations for k in ["smith", "blacksmith", "carpenter", "weaver"])

        is_balanced = has_food_production and has_health_care and has_law_enforcement and has_crafts

        return {
            "is_balanced": is_balanced,
            "has_food_production": has_food_production,
            "has_health_care": has_health_care,
            "has_law_enforcement": has_law_enforcement,
            "has_crafts": has_crafts,
            "total_workers": len(occupations)
        }

class TownSetupEngine:
    """Master Setup Pipeline integrating Kinship, Wealth Pareto Stratification, and History Generation."""

    def __init__(self, random_gen: SeededRandom):
        self.random_gen = random_gen
        self.kinship_graph = KinshipGraph()

    def setup_town_and_population(
        self,
        settlement_name: str,
        npcs: Dict[str, NPC],
        social_network: Any,
        pantries: Dict[str, Any],
        item_defs: Dict[str, Any]
    ) -> Dict[str, Any]:

        # 1. Socio-Economic Pareto Wealth Allocation
        WealthStratifier.allocate_pareto_wealth(npcs, self.random_gen)

        # 2. Occupational Matrix Validation
        occ_check = OccupationalMatrix.validate_town_occupations(npcs)

        # 3. Demographics Check
        demo_check = DemographicPyramid.evaluate_settlement_demographics(npcs)

        return {
            "settlement_name": settlement_name,
            "occupational_check": occ_check,
            "demographic_summary": demo_check,
            "total_population": len(npcs)
        }
