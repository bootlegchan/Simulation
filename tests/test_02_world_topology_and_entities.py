"""
Consolidated Test Suite 02: Entities, World Topology, Spatial Pathfinding, Steering, Permissions, and Mutations.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.item import ItemDefinition, ItemInstance
from src.entities.object import InteractiveObject
from src.world.topology import WeightedNodeTopology, SpatialNode
from src.world.spatial_index import SpatialGridIndex
from src.world.steering import SteeringAgent, Vector2D
from src.world.permissions import PermissionsEngine
from src.world.mutation import WorldMutationEngine
from src.world.self_contained import LocalResourceNode, SelfContainedEcosystemEngine


class TestWorldTopologyAndEntities(unittest.TestCase):
    """Verifies entity lifecycles, spatial graph topology, pathfinding, steering, and resource nodes."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_item_and_object_entity_instantiation(self):
        item_def = ItemDefinition("item_bread", "Loaf of Bread", "food", base_value=12.0, spoil_rate=0.5)
        item_inst = ItemInstance("inst_1", "item_bread", freshness=100.0, durability=100.0, quality=1.2)

        self.assertEqual(item_def.base_value, 12.0)
        self.assertEqual(item_inst.freshness, 100.0)

        obj = InteractiveObject("obj_chest", "Wooden Chest", capabilities=["store"])
        self.assertTrue(obj.has_capability("store"))

    def test_weighted_node_topology_pathfinding_and_caching(self):
        topology = WeightedNodeTopology()

        node_a = SpatialNode("node_a", "Square", "room", connected_node_ids=["node_b"])
        node_b = SpatialNode("node_b", "Hallway", "room", connected_node_ids=["node_a", "node_c"], traversal_cost_modifier=1.5)
        node_c = SpatialNode("node_c", "Bedroom", "room", connected_node_ids=["node_b"])

        topology.register_node(node_a)
        topology.register_node(node_b)
        topology.register_node(node_c)

        path = topology.find_shortest_weighted_path("node_a", "node_c")
        self.assertEqual(path, ["node_a", "node_b", "node_c"])

        weight = topology.get_travel_weight("node_a", "node_c")
        self.assertGreater(weight, 1.0)
        self.assertTrue(topology.is_accessible("node_a", "node_c", threshold=50.0))

    def test_spatial_grid_index_steering_and_vision_cones(self):
        grid = SpatialGridIndex(cell_size=10.0)
        grid.update_entity_position("agent_1", 5.0, 5.0)
        grid.update_entity_position("agent_2", 8.0, 8.0)
        grid.update_entity_position("agent_3", 50.0, 50.0)

        nearby = grid.get_nearby_entities(5.0, 5.0, radius=10.0)
        self.assertIn("agent_1", nearby)
        self.assertIn("agent_2", nearby)
        self.assertNotIn("agent_3", nearby)

        agent = SteeringAgent("agent_1", Vector2D(0.0, 0.0), facing_angle_deg=0.0)
        target_vec = Vector2D(10.0, 0.0)
        steered_pos = agent.seek_and_steer(target_vec)
        self.assertGreater(steered_pos.x, 0.0)

        in_vision = agent.is_in_perception_cone(target_vec)
        self.assertTrue(in_vision)

    def test_permissions_engine_access_rules(self):
        thaddeus = self.engine.npcs.get("npc_thaddeus")
        lib_shelf = self.engine.objects.get("obj_library_bookshelf")

        if thaddeus and lib_shelf:
            perm = PermissionsEngine.can_access_object(thaddeus, lib_shelf)
            self.assertIn("allowed", perm)

    def test_world_mutation_engine_and_building_construction(self):
        settlement = self.engine.settlements["settlement_oakwood"]
        initial_bldgs = len(settlement.buildings)

        building_data = {
            "id": "bldg_granary_new",
            "name": "New Granary",
            "settlement_id": settlement.id,
            "rooms": {
                "room_grain_vault": {
                    "id": "room_grain_vault",
                    "name": "Grain Vault",
                    "building_id": "bldg_granary_new",
                    "connected_room_ids": []
                }
            }
        }

        mutation_engine = WorldMutationEngine(self.engine.event_bus)
        res = mutation_engine.construct_building(
            settlement=settlement,
            building_data=building_data,
            spatial_graph=self.engine.spatial_graph,
            spatial_grid=None,
            objects=self.engine.objects
        )

        self.assertTrue(res["success"])
        self.assertIn("bldg_granary_new", settlement.buildings)
        self.assertEqual(len(settlement.buildings), initial_bldgs + 1)

    def test_self_contained_natural_resource_nodes_and_harvesting(self):
        eco_engine = SelfContainedEcosystemEngine()
        aldous = self.engine.npcs["npc_aldous"]

        harvest_res = eco_engine.process_harvest("node_forest_timber", aldous.id, aldous.inventory, harvest_amount=10.0)
        self.assertTrue(harvest_res["success"])
        self.assertEqual(harvest_res["harvested_qty"], 10.0)

        # Daily replenishment
        replenished = eco_engine.process_daily_replenishment()
        self.assertIn("node_forest_timber", replenished)


if __name__ == "__main__":
    unittest.main()
