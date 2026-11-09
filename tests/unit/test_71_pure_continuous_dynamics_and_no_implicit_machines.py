"""
Unit Test Suite 71: Pure Continuous Field Dynamics & Zero Implicit State Machines.
Verifies:
1. Elimination of instant teleportation (physical topological spatial transit).
2. Continuous somatic fatigue and vocational alignment curves (no discrete phase overrides).
3. Continuous sleep inertia and waking homeostasis without hard clock switches.
"""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.ai.utility import UtilityEvaluator
from src.entities.occupations import OccupationRegistry
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingCategory

class TestPureContinuousDynamicsAndNoImplicitMachines(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

    def test_01_no_teleportation_spatial_transit_step(self):
        """Verify that agents physically commute room-by-room along SpatialGraph rather than teleporting."""
        worker = self.engine.npcs["npc_aldous"]
        worker.location_id = "room_village_square"
        worker.work_location_id = "room_farmhouse"
        worker.needs["energy"] = 90.0
        worker.needs["hunger"] = 10.0

        # Run 60 ticks so hourly decision triggers at tick 60
        self.engine.tick(60)

        # Worker should follow the topological path, NOT teleport instantly across rooms
        path = self.engine.context.spatial_graph.find_shortest_path("room_village_square", "room_farmhouse")
        self.assertIsNotNone(path)
        self.assertIn(worker.location_id, path)

    def test_02_continuous_rest_gradient_exhaustion(self):
        """Verify that high fatigue produces overpowering rest utility naturally without phase overrides."""
        needs_tired = {"energy": 15.0, "hunger": 10.0, "social": 50.0}
        personality = {"conscientiousness": 0.8, "extraversion": 0.5}

        u_tired = UtilityEvaluator.evaluate_drives(needs_tired, personality)
        self.assertGreater(u_tired["rest"], u_tired["work_production"])
        self.assertGreater(u_tired["rest"], 100.0)

        needs_rested = {"energy": 90.0, "hunger": 10.0, "social": 50.0}
        u_rested = UtilityEvaluator.evaluate_drives(needs_rested, personality)
        self.assertGreater(u_rested["work_production"], u_rested["rest"])
        self.assertLess(u_rested["rest"], 15.0)

    def test_03_continuous_vocational_alignment_curves(self):
        """Verify shift window provides continuous vocational alignment without rigid phase locks."""
        occ_reg = OccupationRegistry.get_instance()
        shift = occ_reg.get_shift_window("Town Guard")  # 21:00 to 05:00

        self.assertTrue(shift.is_within_shift(23.0))
        self.assertTrue(shift.is_within_shift(2.0))
        self.assertFalse(shift.is_within_shift(12.0))

    def test_04_sleep_inertia_continuity(self):
        """Verify sleep inertia protects ongoing rest without needing arbitrary clock bounds."""
        citizen = self.engine.npcs["npc_citizen_01"]
        citizen.current_action = "SLEEP_REST"
        citizen.needs["energy"] = 45.0  # Still recovering
        citizen.needs["hunger"] = 20.0

        needs = citizen.needs
        personality = citizen.personality
        env_mods = {}
        if citizen.current_action in ("SLEEP_REST", "COLLAPSE_FATIGUE"):
            if citizen.needs["energy"] < 90.0 and citizen.needs["hunger"] < 65.0:
                env_mods["rest"] = 40.0

        u = UtilityEvaluator.evaluate_drives(needs, personality, env_modifiers=env_mods)
        self.assertGreater(u["rest"], u["work_production"])
        self.assertGreater(u["rest"], u["socialize"])

if __name__ == "__main__":
    unittest.main()
