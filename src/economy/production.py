from typing import Any, Dict, List, Optional
from src.entities.item import ItemDefinition, ItemInstance

class Recipe:
    """Production recipe mapping inputs -> outputs at required capability workstations."""

    def __init__(
        self,
        recipe_id: str,
        name: str,
        inputs: Dict[str, int],
        outputs: Dict[str, int],
        required_capability: str,
        processing_ticks: int = 1,
        quality_multiplier: float = 1.0,
    ):
        self.id = recipe_id
        self.name = name
        self.inputs = inputs  # item_def_id -> quantity
        self.outputs = outputs  # item_def_id -> quantity
        self.required_capability = required_capability
        self.processing_ticks = processing_ticks
        self.quality_multiplier = quality_multiplier

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recipe":
        return cls(
            recipe_id=data["id"],
            name=data["name"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            required_capability=data["required_capability"],
            processing_ticks=data.get("processing_ticks", 1),
            quality_multiplier=data.get("quality_multiplier", 1.0),
        )

class ProductionManager:
    """Handles production execution and material crafting."""

    @staticmethod
    def can_craft(npc_inventory: List[ItemInstance], recipe: Recipe) -> bool:
        inv_counts: Dict[str, int] = {}
        for item in npc_inventory:
            inv_counts[item.item_def_id] = inv_counts.get(item.item_def_id, 0) + 1
        for item_id, required_qty in recipe.inputs.items():
            if inv_counts.get(item_id, 0) < required_qty:
                return False
        return True

    @staticmethod
    def craft(npc_inventory: List[ItemInstance], recipe: Recipe, crafter_id: str) -> List[ItemInstance]:
        # Consume inputs
        for item_id, required_qty in recipe.inputs.items():
            removed = 0
            to_remove = []
            for item in npc_inventory:
                if item.item_def_id == item_id and removed < required_qty:
                    to_remove.append(item)
                    removed += 1
            for item in to_remove:
                npc_inventory.remove(item)

        # Produce outputs
        new_items = []
        import uuid
        for item_id, produce_qty in recipe.outputs.items():
            for _ in range(produce_qty):
                inst = ItemInstance(
                    instance_id=f"inst_{uuid.uuid4().hex[:8]}",
                    item_def_id=item_id,
                    freshness=100.0,
                    durability=100.0,
                    quality=recipe.quality_multiplier,
                    owner_id=crafter_id,
                )
                npc_inventory.append(inst)
                new_items.append(inst)
        return new_items
