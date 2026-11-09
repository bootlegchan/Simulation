"""Simulation Suite 04: Cross-Scenario Isolation and Multi-Run Benchmarking."""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine

class TestMultiRunSixMonthExperiment(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()

    def test_01_cross_scenario_isolation(self):
        engine_oak = SimulationEngine(self.data_dir)
        engine_oak.initialize(seed=42, scenario_filename="oakwood_baseline.json")
        self.assertIn("npc_aldous", engine_oak.npcs)

        engine_iron = SimulationEngine(self.data_dir)
        engine_iron.initialize(seed=777, scenario_filename="ironreach_frontier.json")
        self.assertIn("npc_captain_morgren", engine_iron.npcs)
        self.assertNotIn("npc_aldous", engine_iron.npcs)

    def test_02_pack_mounting_integrity(self):
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        res = engine.mount_pack("chandler_and_apiary")
        self.assertTrue(res["mounted"])
        self.assertIn("npc_corin_apiarist", engine.npcs)
        self.assertIn("beeswax_candle", engine.item_definitions)

if __name__ == "__main__":
    unittest.main()
