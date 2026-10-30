from typing import Any, Dict, List
from src.entities.npc import NPC

class MacroEconomicTracker:
    """Tracks macro-economic indicators: money supply, Consumer Price Index (CPI), and Gini coefficient."""

    @staticmethod
    def calculate_total_currency(npcs: Dict[str, NPC], municipal_treasury_vault: float = 0.0) -> float:
        total_npc_wealth = sum(npc.wealth for npc in npcs.values())
        return total_npc_wealth + municipal_treasury_vault

    @staticmethod
    def calculate_gini_coefficient(npcs: Dict[str, NPC]) -> float:
        """Calculate Gini coefficient of wealth inequality (0.0 = total equality, 1.0 = total inequality)."""
        wealths = sorted([npc.wealth for npc in npcs.values()])
        n = len(wealths)
        if n == 0 or sum(wealths) == 0:
            return 0.0

        numerator = sum((i + 1) * w for i, w in enumerate(wealths))
        denominator = n * sum(wealths)
        return (2 * numerator) / denominator - (n + 1) / n

    @staticmethod
    def calculate_cpi(current_item_prices: Dict[str, float], baseline_item_prices: Dict[str, float]) -> float:
        """Calculate Consumer Price Index relative to baseline (100.0 = baseline index)."""
        if not baseline_item_prices:
            return 100.0

        total_current = 0.0
        total_baseline = 0.0

        for item_id, base_p in baseline_item_prices.items():
            curr_p = current_item_prices.get(item_id, base_p)
            total_current += curr_p
            total_baseline += base_p

        if total_baseline == 0:
            return 100.0

        return (total_current / total_baseline) * 100.0
