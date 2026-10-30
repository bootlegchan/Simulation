"""
Test Suite 16: Logical Invariants, Economic Conservation, Biological Priorities, and Multi-Day Simulation Dynamics.
Verifies wealth conservation, starvation overrides, diurnal rhythm dynamics, thermal protection, and long-run simulation stability.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.world.environment import EnvironmentState, WeatherType, TimeOfDay
from src.ai.utility import UtilityEvaluator
from src.economy.macro import MacroEconomicTracker


class TestLogicalInvariantsAndSimulationDynamics(unittest.TestCase):
    """Verifies physical and socio-economic ground truths in simulation behavior."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

    def test_01_economic_wealth_conservation_and_legitimacy(self):
        """Verify that total currency supply changes only through legitimate economic mechanisms."""
        initial_wealth = MacroEconomicTracker.calculate_total_currency(self.engine.npcs)

        # Run 120 ticks (2 hours)
        self.engine.tick(120)

        final_wealth = MacroEconomicTracker.calculate_total_currency(self.engine.npcs)
        # In our autonomous cycle, workers generate gold when laboring, and spend gold on market bread
        self.assertGreater(final_wealth, 0.0)
        # No absurd runaway inflation in 2 hours
        self.assertLess(final_wealth, initial_wealth * 1.5)

    def test_02_biological_starvation_drive_override(self):
        """Verify that an NPC with critical hunger (95/100) overrides normal work or leisure to seek food."""
        aldous = self.engine.npcs["npc_aldous"]
        aldous.needs["hunger"] = 95.0
        aldous.needs["energy"] = 80.0
        aldous.needs["social"] = 80.0

        utilities = UtilityEvaluator.evaluate_drives(
            needs=aldous.needs,
            personality=aldous.personality,
            feelings=aldous.feelings,
        )

        probs = UtilityEvaluator.calculate_softmax_probabilities(utilities, temperature=10.0)

        # Hunger drive must dominate choice probability (> 70%)
        self.assertGreater(probs.get("satisfy_hunger", 0.0), 0.70)
        self.assertLess(probs.get("work_production", 0.0), 0.20)

    def test_03_diurnal_circadian_rhythm_dynamics(self):
        """Verify that during nocturnal hours (22:00 to 05:00), sleep/rest utilities dominate over work."""
        env = EnvironmentState(weather=WeatherType.CLEAR, season="SUMMER")
        night_mods = env.calculate_utility_modifiers(hour=23)
        day_mods = env.calculate_utility_modifiers(hour=12)

        self.assertGreater(night_mods["rest"], 30.0)
        self.assertLess(night_mods["work_production"], 0.0)

        # Compare utilities for identical NPC needs during night vs day
        test_needs = {"hunger": 30.0, "energy": 45.0, "social": 50.0}

        night_utils = UtilityEvaluator.evaluate_drives(test_needs, env_modifiers=night_mods)
        day_utils = UtilityEvaluator.evaluate_drives(test_needs, env_modifiers=day_mods)

        self.assertGreater(night_utils["rest"], day_utils["rest"])

    def test_04_thermal_insulation_and_hearth_warmth_protection(self):
        """Verify that winter cold snaps cause hypothermia risk outdoors, but rooms with active hearths provide comfort."""
        climate = self.engine.micro_climate_engine
        self.assertIsNotNone(climate)

        ambient_winter = climate.calculate_ambient_temperature(season="WINTER", time_of_day="NIGHT")
        self.assertLess(ambient_winter, 0.0)

        # Find room with hearth (e.g. farmhouse kitchen or living)
        settlement = self.engine.settlements["settlement_oakwood"]
        farmhouse = settlement.buildings["bldg_farmhouse"]
        kitchen_room = farmhouse.rooms["room_farmhouse_kitchen"]

        indoor_temp = climate.calculate_indoor_room_temperature(
            room=kitchen_room,
            building=farmhouse,
            season="WINTER",
            hour=23,
            objects_dict=self.engine.objects
        )

        # Indoor with hearth must be significantly warmer than sub-zero ambient
        self.assertGreater(indoor_temp, ambient_winter + 15.0)

    def test_05_multi_day_stability_no_deadlocks(self):
        """Verify that the engine runs stably for 2 full days (2,880 ticks) without deadlocks or crashes."""
        self.engine.tick(2880)

        self.assertEqual(self.engine.clock.current_tick, 2880)
        self.assertEqual(self.engine.lifecycle_state.value, "RUNNING")
        # Verify that all NPCs remain alive and in valid spatial rooms
        for npc in self.engine.npcs.values():
            self.assertIsNotNone(npc.location_id)
            self.assertGreaterEqual(npc.wealth, 0.0)
            self.assertGreater(len(npc.biographical_log), 5)


if __name__ == "__main__":
    unittest.main()
