"""
Self-Contained Local Resource Nodes and Local Labor Allocation Engine.
Eliminates external trade dependencies by establishing local raw material nodes
(Oakwood Ancient Forest, Granite Stone Quarry, River Basin Clay Deposit) and local job creation loops.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid
from src.entities.item import ItemInstance

@dataclass
class LocalResourceNode:
    node_id: str
    name: str
    resource_type: str  # "timber", "granite_stone", "clay_and_fish", "wild_herbs"
    max_capacity: float = 500.0
    current_capacity: float = 500.0
    replenishment_rate_per_day: float = 15.0
    harvest_tool_required: str = "axe"  # "axe", "pickaxe", "bucket", "sickle"

    def harvest_resource(self, amount: float = 10.0) -> float:
        harvested = min(self.current_capacity, amount)
        self.current_capacity -= harvested
        return harvested

    def replenish_daily(self) -> float:
        self.current_capacity = min(self.max_capacity, self.current_capacity + self.replenishment_rate_per_day)
        return self.current_capacity

class SelfContainedEcosystemEngine:
    """Manages local raw material harvesting nodes and local job creation/apprentice training loops."""

    def __init__(self):
        self.resource_nodes: Dict[str, LocalResourceNode] = {
            "node_forest_timber": LocalResourceNode(
                node_id="node_forest_timber",
                name="Oakwood Ancient Forest",
                resource_type="timber",
                harvest_tool_required="axe"
            ),
            "node_granite_quarry": LocalResourceNode(
                node_id="node_granite_quarry",
                name="Oakwood Granite Quarry",
                resource_type="granite_stone",
                harvest_tool_required="pickaxe"
            ),
            "node_river_basin": LocalResourceNode(
                node_id="node_river_basin",
                name="Oakwood River Basin",
                resource_type="clay_and_fish",
                harvest_tool_required="bucket"
            ),
        }

    def process_harvest(
        self,
        node_id: str,
        harvester_id: str,
        harvester_inventory: List[ItemInstance],
        harvest_amount: float = 10.0
    ) -> Dict[str, Any]:
        """Harvests raw materials locally and appends newly generated raw item instances to inventory."""
        if node_id not in self.resource_nodes:
            return {"success": False, "reason": "Unknown resource node"}

        node = self.resource_nodes[node_id]
        harvested_qty = node.harvest_resource(harvest_amount)

        if harvested_qty <= 0.0:
            return {"success": False, "reason": "Resource node depleted"}

        # Create raw item instances
        item_def_map = {
            "timber": "raw_timber",
            "granite_stone": "granite_block",
            "clay_and_fish": "river_clay"
        }
        item_def_id = item_def_map.get(node.resource_type, "raw_timber")

        new_items = []
        for _ in range(int(harvested_qty // 2.0)):
            inst = ItemInstance(
                instance_id=f"inst_harvest_{uuid.uuid4().hex[:8]}",
                item_def_id=item_def_id,
                freshness=100.0,
                durability=100.0,
                quality=1.0,
                owner_id=harvester_id
            )
            harvester_inventory.append(inst)
            new_items.append(inst)

        return {
            "success": True,
            "node_name": node.name,
            "harvested_qty": harvested_qty,
            "items_produced": len(new_items),
            "remaining_capacity": node.current_capacity
        }

    def process_daily_replenishment(self) -> Dict[str, float]:
        """Replenishes all local natural resource nodes at daily tick intervals."""
        return {
            node_id: node.replenish_daily()
            for node_id, node in self.resource_nodes.items()
        }
