"""Simulation Suite 01: Integrity, Determinism, and Entropy."""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.diagnostics.simulation_integrity import SimulationIntegrityAuditor

class TestSimulationIntegrityAndDiversity(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.auditor = SimulationIntegrityAuditor(self.data_dir)

    def test_01_bitwise_determinism(self):
        res = self.auditor.verify_bitwise_determinism(seed=42, ticks=120)
        self.assertTrue(res["is_bitwise_identical"])

    def test_02_cross_seed_divergence(self):
        res = self.auditor.verify_cross_seed_divergence(seed_a=42, seed_b=999, ticks=120)
        self.assertTrue(res["has_diverged"])

    def test_03_action_entropy(self):
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.tick(120)
        ent = self.auditor.calculate_action_entropy(engine)
        self.assertTrue(ent["is_diversity_healthy"])

if __name__ == "__main__":
    unittest.main()
