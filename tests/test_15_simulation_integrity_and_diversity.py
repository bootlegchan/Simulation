"""
Test Suite 15: Simulation Integrity, Replay Determinism, Trajectory Divergence, and Entropy.
Verifies bitwise reproducibility for identical seeds, trajectory divergence across distinct seeds,
action choice Shannon entropy, and state space coverage.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.diagnostics.simulation_integrity import SimulationIntegrityAuditor


class TestSimulationIntegrityAndDiversity(unittest.TestCase):
    """Verifies that the simulation is 100% deterministic on same seeds, but non-trivially diverse on different seeds."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.auditor = SimulationIntegrityAuditor(self.data_dir)

    def test_01_bitwise_determinism_identical_seed(self):
        """Verify that two simulation runs with identical seeds produce bit-for-bit identical outcomes."""
        res = self.auditor.verify_bitwise_determinism(seed=42, ticks=180)
        self.assertTrue(res["is_bitwise_identical"])
        self.assertEqual(res["gini_delta"], 0.0)
        self.assertEqual(res["wealth_delta"], 0.0)
        self.assertTrue(res["events_match"])
        self.assertEqual(res["npc_state_divergences"], 0)

    def test_02_cross_seed_trajectory_divergence(self):
        """Verify that distinct seeds produce divergent action choices, wealth vectors, and events."""
        res = self.auditor.verify_cross_seed_divergence(seed_a=42, seed_b=999, ticks=180)
        self.assertTrue(res["has_diverged"])
        self.assertLess(res["jaccard_event_similarity"], 0.95)
        self.assertGreater(res["wealth_euclidean_distance"], 5.0)

    def test_03_action_choice_shannon_entropy(self):
        """Verify that autonomous action choices maintain healthy Shannon entropy (H > 1.2 bits) avoiding robotic monoculture."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(180)

        entropy_res = self.auditor.calculate_action_entropy(engine)
        self.assertTrue(entropy_res["is_diversity_healthy"])
        self.assertGreater(entropy_res["shannon_entropy"], 1.2)
        self.assertGreaterEqual(entropy_res["unique_action_types"], 3)

    def test_04_spatial_state_space_coverage(self):
        """Verify that autonomous NPCs disperse and utilize rooms throughout the settlement."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(180)

        coverage_res = self.auditor.calculate_state_space_coverage(engine)
        self.assertGreater(coverage_res["visited_rooms_count"], 1)
        self.assertGreater(coverage_res["room_coverage_ratio"], 0.05)

    def test_05_longitudinal_divergence_scaling(self):
        """Verify that divergence between distinct seeds scales over time rather than collapsing into a single attractor."""
        res_short = self.auditor.verify_cross_seed_divergence(seed_a=42, seed_b=999, ticks=60)
        res_long = self.auditor.verify_cross_seed_divergence(seed_a=42, seed_b=999, ticks=240)

        self.assertTrue(res_short["has_diverged"])
        self.assertTrue(res_long["has_diverged"])
        # As time progresses, more unique events occur, lowering Jaccard event overlap
        self.assertLessEqual(res_long["jaccard_event_similarity"], res_short["jaccard_event_similarity"] + 0.05)


if __name__ == "__main__":
    unittest.main()
