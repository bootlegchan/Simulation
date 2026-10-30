"""
Test Suite 11: Dynamic Settlement Growth, Intelligent Zoning, Path Generation,
Building Condition Degradation/Repair, and Functional Object Placement.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.world.urban_growth import UrbanGrowthEngine, BuildingCondition
from src.world.model import Building, Room


class TestDynamicSettlementGrowthAndPlacement(unittest.TestCase):
    """Verifies file-based urban planning, zoning, road expansion, lifecycle decay, and anchor object placement."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.settlement = self.engine.settlements["settlement_oakwood"]
        self.growth_engine = self.engine.urban_growth_engine

    def test_01_urban_planning_and_placement_rules_loaded(self):
        """Verify urban planning config, placement rules, and blueprints are loaded from JSON files."""
        self.assertIsNotNone(self.growth_engine)
        self.assertIn("DISTRICT_RESIDENTIAL", self.growth_engine.districts_cfg)
        self.assertIn("DISTRICT_COMMERCIAL_ARTISAN", self.growth_engine.districts_cfg)
        self.assertIn("DISTRICT_CIVIC_MARKET", self.growth_engine.districts_cfg)
        self.assertIn("DISTRICT_INDUSTRIAL_OUTSKIRTS", self.growth_engine.districts_cfg)

        # Placement rules
        self.assertIn("room_archetypes", self.growth_engine.placement_rules)
        self.assertIn("anchor_rules", self.growth_engine.placement_rules)
        self.assertIn("object_canopy_bed", self.growth_engine.placement_rules["anchor_rules"])

        # Blueprints
        self.assertIn("blueprint_residential_cottage", self.growth_engine.blueprints)
        self.assertIn("blueprint_merchant_villa", self.growth_engine.blueprints)
        self.assertIn("blueprint_artisan_workshop", self.growth_engine.blueprints)

    def test_02_intelligent_zoning_and_road_attachment(self):
        """Verify buildings connect to specific district roads rather than scattering randomly."""
        district_res, road_res = self.growth_engine.determine_target_district_and_road("RESIDENTIAL", self.settlement)
        self.assertEqual(district_res, "DISTRICT_RESIDENTIAL")
        self.assertIn("lane_residential", road_res)

        district_com, road_com = self.growth_engine.determine_target_district_and_road("COMMERCIAL", self.settlement)
        self.assertEqual(district_com, "DISTRICT_COMMERCIAL_ARTISAN")
        self.assertIn("row_craftsmen", road_com)

        # Verify new road room is connected to village square
        self.assertIn(road_res, self.settlement.buildings[f"bldg_road_lane_residential_1"].rooms)
        road_room = self.settlement.buildings[f"bldg_road_lane_residential_1"].rooms[road_res]
        self.assertIn("room_village_square", road_room.connected_room_ids)

    def test_03_functional_object_placement_and_anchors(self):
        """Verify constructing a cottage places functional anchor objects based on room archetypes."""
        construct_res = self.growth_engine.execute_intelligent_construction(
            settlement=self.settlement,
            blueprint_id="blueprint_residential_cottage",
            spatial_graph=self.engine.spatial_graph,
            objects_dict=self.engine.objects,
            owner_id="npc_aldous"
        )

        self.assertTrue(construct_res["success"])
        bldg_id = construct_res["building_id"]
        self.assertIn(bldg_id, self.settlement.buildings)
        building = self.settlement.buildings[bldg_id]

        # Verify building condition and category
        self.assertEqual(building.category, "RESIDENTIAL")
        self.assertEqual(building.condition_state, BuildingCondition.PRISTINE.value)
        self.assertEqual(building.structural_integrity, 100.0)

        # Check rooms created
        self.assertEqual(len(building.rooms), 2)
        living_room = next(r for r in building.rooms.values() if "living" in r.id)
        bed_room = next(r for r in building.rooms.values() if "bedroom" in r.id)

        # Verify intelligent object placement in rooms
        self.assertTrue(len(living_room.contained_object_ids) > 0)
        self.assertTrue(len(bed_room.contained_object_ids) > 0)

        # Verify anchored capabilities
        living_objs = [self.engine.objects[oid] for oid in living_room.contained_object_ids]
        bed_objs = [self.engine.objects[oid] for oid in bed_room.contained_object_ids]

        self.assertTrue(any(o.has_capability("family_gathering") for o in living_objs))
        self.assertTrue(any(o.has_capability("sleep") for o in bed_objs))

    def test_04_economic_building_degradation_and_ruins(self):
        """Verify that lack of maintenance causes buildings to degrade to DILAPIDATED, CONDEMNED, and RUINS."""
        # Create an unmaintained building with 0 wealth owner and 0 municipal treasury
        test_bldg = Building(
            building_id="bldg_test_shack",
            name="Test Neglected Shack",
            settlement_id=self.settlement.id,
            rooms={
                "room_shack_inner": Room("room_shack_inner", "Shack Room", "bldg_test_shack", occupant_ids=["npc_barnaby_beggar"])
            },
            category="RESIDENTIAL",
            structural_integrity=30.0,
            condition_state=BuildingCondition.DILAPIDATED.value,
            owner_id="npc_barnaby_beggar"  # Penniless beggar
        )
        self.settlement.buildings["bldg_test_shack"] = test_bldg
        self.engine.npcs["npc_barnaby_beggar"].wealth = 0.0
        self.engine.municipal_treasury.balance = 0.0

        # Simulate 3 daily degradation cycles
        for tick in [1440, 2880, 4320]:
            lifecycle_res = self.growth_engine.process_daily_lifecycle(
                settlement=self.settlement,
                npcs=self.engine.npcs,
                municipal_treasury=self.engine.municipal_treasury,
                current_tick=tick,
                economic_multiplier=2.0  # Accelerated economic depression
            )

        self.assertLess(test_bldg.structural_integrity, 25.0)
        self.assertIn(test_bldg.condition_state, (BuildingCondition.CONDEMNED.value, BuildingCondition.RUINS.value))

    def test_05_economic_prosperity_and_building_repair(self):
        """Verify that funded maintenance restores structural integrity and maintains PRISTINE condition."""
        vance_manor = self.settlement.buildings["bldg_vance_manor"]
        vance_manor.structural_integrity = 70.0
        vance_manor.condition_state = BuildingCondition.MAINTAINED.value
        vance_manor.owner_id = "npc_marcus_vance"
        self.engine.npcs["npc_marcus_vance"].wealth = 500.0  # Wealthy merchant

        lifecycle_res = self.growth_engine.process_daily_lifecycle(
            settlement=self.settlement,
            npcs=self.engine.npcs,
            municipal_treasury=self.engine.municipal_treasury,
            current_tick=1440
        )

        self.assertGreater(vance_manor.structural_integrity, 70.0)
        self.assertGreater(lifecycle_res["maintained_count"], 0)

    def test_06_demolition_and_urban_redevelopment(self):
        """Verify demolition removes rooms and cleans up spatial graph for redevelopment."""
        # Create a condemned test building
        bldg_id = "bldg_condemned_tenement"
        condemned_bldg = Building(
            building_id=bldg_id,
            name="Condemned Tenement",
            settlement_id=self.settlement.id,
            rooms={
                "room_condemned_1": Room("room_condemned_1", "Rotten Room", bldg_id, connected_room_ids=["room_village_square"])
            },
            structural_integrity=5.0,
            condition_state=BuildingCondition.CONDEMNED.value
        )
        self.settlement.buildings[bldg_id] = condemned_bldg
        self.engine.spatial_graph.build_graph(self.engine.settlements)
        self.assertIn("room_condemned_1", self.engine.spatial_graph.adj)

        demolish_res = self.growth_engine.demolish_condemned_building(
            settlement=self.settlement,
            building_id=bldg_id,
            spatial_graph=self.engine.spatial_graph,
            objects_dict=self.engine.objects,
            npcs=self.engine.npcs
        )

        self.assertTrue(demolish_res["success"])
        self.assertNotIn(bldg_id, self.settlement.buildings)
        self.assertNotIn("room_condemned_1", self.engine.spatial_graph.adj)


if __name__ == "__main__":
    unittest.main()
