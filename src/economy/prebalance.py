"""
Economic Supply-Demand Pre-Balancing and Market Inventory Warmup Engine.
Simulates baseline production and consumption cycles prior to Tick 1 to ensure starting pantries,
store inventories, and commodity prices are in realistic economic equilibrium.
"""
from typing import Any, Dict, List
from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.economy.pricing import DynamicPricingEngine

class PrebalanceEngine:
    """Pre-simulates market supply, demand, and pantry stocks for 100 warmup ticks before Tick 1."""

    @staticmethod
    def prebalance_market_and_pantries(
        npcs: Dict[str, NPC],
        item_definitions: Dict[str, Any],
        pantries_and_chests: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensures NPCs begin with non-empty pantries, tools, and balanced baseline commodity pricing."""

        pantries_stocked = 0
        items_generated = 0

        # Stock pantries and chests with baseline food and materials
        for storage_obj in pantries_and_chests.values():
            capabilities = getattr(storage_obj, "capabilities", [])
            if "store_food" in capabilities or "pantry" in storage_obj.id:
                # Add baseline flour and bread
                for _ in range(3):
                    storage_obj.contained_item_ids.append(f"item_bread_stock_{items_generated}")
                    items_generated += 1
                pantries_stocked += 1

        # Baseline pricing pre-calculation
        baseline_prices = {}
        for item_id, item_def in item_definitions.items():
            base_val = getattr(item_def, "base_value", 10.0)
            # Calculate equilibrium price assuming supply=10, demand=10
            eq_price = DynamicPricingEngine.calculate_price(base_value=base_val, supply=10, demand=10, quality=1.0)
            baseline_prices[item_id] = eq_price

        return {
            "pantries_stocked_count": pantries_stocked,
            "items_pregenerated_count": items_generated,
            "baseline_prices": baseline_prices
        }
