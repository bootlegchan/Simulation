from typing import Dict, List
from src.entities.item import ItemDefinition, ItemInstance

class SpoilageTracker:
    """Manages food item freshness decay and degradation."""

    @staticmethod
    def apply_spoilage(items: List[ItemInstance], item_defs: Dict[str, ItemDefinition], in_pantry: bool = False) -> List[ItemInstance]:
        decay_factor = 0.2 if in_pantry else 1.0
        spoiled_items = []
        for item in items:
            item_def = item_defs.get(item.item_def_id)
            if item_def and item_def.spoil_rate > 0:
                item.freshness -= item_def.spoil_rate * decay_factor
                if item.freshness <= 0:
                    spoiled_items.append(item)
        
        for spoiled in spoiled_items:
            items.remove(spoiled)
        return spoiled_items
