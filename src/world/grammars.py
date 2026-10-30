from enum import Enum
from typing import Any, Dict, List, Optional, Set
from src.world.model import Settlement, Building, Room

class BuildingCategory(Enum):
    CIVIC = "CIVIC"
    MEDICAL = "MEDICAL"
    INDUSTRIAL = "INDUSTRIAL"
    COMMERCIAL = "COMMERCIAL"
    RESIDENTIAL = "RESIDENTIAL"
    SACRED = "SACRED"
    UNDERWORLD = "UNDERWORLD"

class MacroZoningRule:
    """Defines population ratio constraints and topological minimum distance rules for building types."""

    def __init__(
        self,
        category: BuildingCategory,
        max_per_population_ratio: float,  # e.g., 1 per 10 NPCs = 0.10
        max_absolute_count: Optional[int] = None,
        min_topological_distance: Dict[BuildingCategory, int] = None
    ):
        self.category = category
        self.max_per_population_ratio = max_per_population_ratio
        self.max_absolute_count = max_absolute_count
        self.min_topological_distance = min_topological_distance or {}

class MacroZoningGrammar:
    """Evaluates macro settlement zoning rules and infrastructure ratio bounds."""

    def __init__(self):
        self.rules: Dict[BuildingCategory, MacroZoningRule] = {
            BuildingCategory.CIVIC: MacroZoningRule(
                category=BuildingCategory.CIVIC,
                max_per_population_ratio=0.10,  # Max 1 per 10 NPCs
                max_absolute_count=5,
            ),
            BuildingCategory.MEDICAL: MacroZoningRule(
                category=BuildingCategory.MEDICAL,
                max_per_population_ratio=0.05,  # Max 1 per 20 NPCs
                max_absolute_count=3,
            ),
            BuildingCategory.INDUSTRIAL: MacroZoningRule(
                category=BuildingCategory.INDUSTRIAL,
                max_per_population_ratio=0.25,  # 1 per 4 NPCs
                min_topological_distance={BuildingCategory.SACRED: 1}  # Keep blast forges separated from chapels
            ),
            BuildingCategory.UNDERWORLD: MacroZoningRule(
                category=BuildingCategory.UNDERWORLD,
                max_per_population_ratio=0.10,  # 1 per 10 NPCs
                max_absolute_count=3,
                min_topological_distance={BuildingCategory.CIVIC: 1}  # Vice dens secluded from Town Hall
            )
        }

    def validate_settlement_zoning(
        self,
        settlement: Settlement,
        population_count: int,
        spatial_graph: Any
    ) -> Dict[str, Any]:
        """Validates building counts, population ratios, and spatial category distances."""
        violations = []
        category_counts: Dict[BuildingCategory, int] = {cat: 0 for cat in BuildingCategory}
        building_categories: Dict[str, BuildingCategory] = {}

        # Classify buildings
        for bldg_id, bldg in settlement.buildings.items():
            b_name = bldg.name.lower()
            if any(k in b_name for k in ["mayor", "town hall", "council", "guard", "dungeon"]):
                cat = BuildingCategory.CIVIC
            elif any(k in b_name for k in ["infirmary", "hospital", "apothecary", "healing"]):
                cat = BuildingCategory.MEDICAL
            elif any(k in b_name for k in ["forge", "smithy", "mill", "quarry", "granary"]):
                cat = BuildingCategory.INDUSTRIAL
            elif any(k in b_name for k in ["chapel", "church", "sanctuary"]):
                cat = BuildingCategory.SACRED
            elif any(k in b_name for k in ["vice", "gambling", "underworld", "smuggler"]):
                cat = BuildingCategory.UNDERWORLD
            elif any(k in b_name for k in ["store", "shop", "market", "tavern"]):
                cat = BuildingCategory.COMMERCIAL
            else:
                cat = BuildingCategory.RESIDENTIAL

            category_counts[cat] += 1
            building_categories[bldg_id] = cat

        # Check ratio and absolute max constraints
        for cat, rule in self.rules.items():
            count = category_counts.get(cat, 0)
            
            # Absolute max check
            if rule.max_absolute_count is not None and count > rule.max_absolute_count:
                violations.append(
                    f"Macro Violation: Category '{cat.value}' count ({count}) exceeds maximum allowed ({rule.max_absolute_count})."
                )

            # Population ratio check
            allowed_by_ratio = max(1, int(population_count * rule.max_per_population_ratio))
            if count > allowed_by_ratio:
                violations.append(
                    f"Macro Violation: Category '{cat.value}' count ({count}) exceeds population ratio budget ({allowed_by_ratio} for {population_count} NPCs)."
                )

        # Check topological distance constraints between conflicting building categories
        for b1_id, cat1 in building_categories.items():
            rule = self.rules.get(cat1)
            if rule and rule.min_topological_distance:
                for cat2, min_dist in rule.min_topological_distance.items():
                    for b2_id, cat2_found in building_categories.items():
                        if cat2_found == cat2 and b1_id != b2_id:
                            r1 = list(settlement.buildings[b1_id].rooms.keys())[0]
                            r2 = list(settlement.buildings[b2_id].rooms.keys())[0]
                            path = spatial_graph.find_shortest_path(r1, r2)
                            dist = len(path) - 1 if path else 999
                            if dist < min_dist:
                                violations.append(
                                    f"Macro Distance Violation: '{settlement.buildings[b1_id].name}' ({cat1.value}) is only {dist} edges from '{settlement.buildings[b2_id].name}' ({cat2.value}); minimum required is {min_dist}."
                                )

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "category_counts": {k.value: v for k, v in category_counts.items()}
        }
