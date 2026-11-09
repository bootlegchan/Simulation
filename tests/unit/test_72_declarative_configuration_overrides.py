"""Unit Test Suite 72: Declarative Configuration Overrides & Hot Setting Reloading."""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.configuration.settings import SettingsRegistry
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.behaviours.actions import ActionRegistry
from src.economy.taxation import MunicipalTaxEngine
from src.ai.utility import UtilityEvaluator
from src.economy.intelligent_food_selection import IntelligentFoodSelector, DiningCandidate, FoodSourceType, CulinaryPalatePreference

class TestDeclarativeConfigurationOverrides(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.settings = SettingsRegistry.get_instance()
        self.settings.reload_all()

    def tearDown(self):
        # Reset any overrides
        self.settings.reload_all()

    def test_01_all_settings_manifests_loaded(self):
        """Verify that all 6 declarative settings manifests exist and are populated."""
        expected = [
            "physiology",
            "drives",
            "civic_governance",
            "job_posting_rules",
            "culinary_economy",
            "romance_and_bonds",
            "occupations",
            "weather_and_climate",
            "recipes",
            "supply_chains",
            "factions",
            "decrees",
            "social_clubs",
            "fraternal_aid",
            "recreation_games",
            "dilemmas",
            "life_goals",
            "epistemic_system",
            "attentional_mindspace",
            "desire_hierarchy",
            "means_end_volition"
        ]
        for name in expected:
            cfg = self.settings.get(name)
            self.assertIsNotNone(cfg, f"Manifest {name} failed to load.")
            self.assertGreater(len(cfg), 0, f"Manifest {name} is unexpectedly empty.")

    def test_02_dynamic_physiology_override(self):
        """Verify that overriding physiology.json changes sleep recovery without editing Python code."""
        npc = self.engine.npcs["npc_aldous"]
        npc.needs["energy"] = 50.0

        # Default recovery: 14.0 points
        ActionRegistry.sleep(npc)
        self.assertAlmostEqual(npc.needs["energy"], 64.0, places=1)

        # Override recovery rate in settings to 25.0 points
        phys = self.settings.get("physiology")
        orig_rate = phys["sleep_recovery"]["energy_gain_per_hour"]
        try:
            phys["sleep_recovery"]["energy_gain_per_hour"] = 25.0
            self.settings.set_override("physiology", phys)

            npc.needs["energy"] = 50.0
            ActionRegistry.sleep(npc)
            self.assertAlmostEqual(npc.needs["energy"], 75.0, places=1)
        finally:
            phys["sleep_recovery"]["energy_gain_per_hour"] = orig_rate
            self.settings.set_override("physiology", phys)

    def test_03_dynamic_tax_rate_override(self):
        """Verify that overriding civic_governance.json changes tax assessment rate dynamically."""
        tax_eng = MunicipalTaxEngine()
        self.assertEqual(tax_eng.tax_rate, 0.08)

        gov = self.settings.get("civic_governance")
        orig_rate = gov["taxation"]["income_tax_rate"]
        try:
            gov["taxation"]["income_tax_rate"] = 0.15
            self.settings.set_override("civic_governance", gov)

            tax_eng_overridden = MunicipalTaxEngine()
            self.assertEqual(tax_eng_overridden.tax_rate, 0.15)
        finally:
            gov["taxation"]["income_tax_rate"] = orig_rate
            self.settings.set_override("civic_governance", gov)

    def test_04_dynamic_culinary_weights_override(self):
        """Verify that overriding culinary_economy.json shifts food evaluation rankings."""
        npc = self.engine.npcs["npc_aldous"]
        cand1 = DiningCandidate(
            source_type=FoodSourceType.COMMERCIAL_BAKERY,
            source_name="Far Bakery",
            location_id="room_bakery",
            vendor_id=None,
            item_def_id="food_bread",
            price_gold=3.0,
            quality_score=90.0,
            specialty_palate=CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD,
            estimated_distance_hops=5,
            relationship_score=50.0
        )
        cand2 = DiningCandidate(
            source_type=FoodSourceType.DIRECT_PRODUCER,
            source_name="Close Farm",
            location_id="room_farmhouse",
            vendor_id=None,
            item_def_id="food_bread",
            price_gold=3.0,
            quality_score=60.0,
            specialty_palate=CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD,
            estimated_distance_hops=0,
            relationship_score=50.0
        )

        ranked_default = IntelligentFoodSelector.evaluate_and_rank_candidates(npc, [cand1, cand2], emergency_hunger=False)
        self.assertIsNotNone(ranked_default)

        # Override distance hop decay to penalize distance much more heavily
        cul = self.settings.get("culinary_economy")
        orig_decay = cul["scoring_modifiers"]["distance_hop_decay"]
        try:
            cul["scoring_modifiers"]["distance_hop_decay"] = 2.5
            self.settings.set_override("culinary_economy", cul)

            ranked_overridden = IntelligentFoodSelector.evaluate_and_rank_candidates(npc, [cand1, cand2], emergency_hunger=False)
            # The close farm (0 hops) will have a much larger advantage
            self.assertEqual(ranked_overridden[0].source_name, "Close Farm")
        finally:
            cul["scoring_modifiers"]["distance_hop_decay"] = orig_decay
            self.settings.set_override("culinary_economy", cul)

    def test_05_dynamic_drive_temperature_override(self):
        """Verify that decision temperature from drives.json modulates logit probabilities."""
        utilities = {"rest": 100.0, "work_production": 50.0}
        probs_default = UtilityEvaluator.calculate_softmax_probabilities(utilities)
        # Low temperature -> more deterministic
        probs_low_temp = UtilityEvaluator.calculate_softmax_probabilities(utilities, temperature=2.0)
        self.assertGreater(probs_low_temp["rest"], probs_default["rest"])


    def test_06_dynamic_weather_setting_override(self):
        """Verify that overriding weather_and_climate.json dynamically shifts ambient temperatures."""
        clim_eng = self.engine.context.get_service("micro_climate_engine")
        clim_eng.start_day_offset = 0 # Winter baseline
        cfg = self.settings.get("weather_and_climate")
        orig_mean = cfg["climate_system"]["seasons"]["WINTER"]["mean_temp"]
        try:
            cfg["climate_system"]["seasons"]["WINTER"]["mean_temp"] = -15.0
            self.settings.set_override("weather_and_climate", cfg)

            state = clim_eng.update_weather(tick=1140)
            self.assertLess(state.ambient_temperature, -10.0)
        finally:
            cfg["climate_system"]["seasons"]["WINTER"]["mean_temp"] = orig_mean
            self.settings.set_override("weather_and_climate", cfg)

if __name__ == "__main__":
    unittest.main()
