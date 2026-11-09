"""Unit Test Suite 68: Intelligent Decision Architecture & Verified Reforms."""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.intelligent_food_selection import IntelligentFoodSelector, FoodSourceType, CulinaryPalatePreference
from src.economy.taxation import MunicipalTaxEngine
from src.society.courtroom_lawsuits import CourtroomLawsuitEngine

class TestIntelligentDecisionArchitectureAndReforms(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_01_intelligent_food_selection_multi_attribute_scoring(self):
        aldous = self.engine.npcs["npc_aldous"]
        choice = IntelligentFoodSelector.select_best_option(aldous, self.engine.context, emergency_hunger=False)
        self.assertIsNotNone(choice)
        self.assertGreater(choice.utility_score, -100.0)
        self.assertIn(choice.source_type, list(FoodSourceType))

    def test_02_palate_and_bakery_aroma_influence(self):
        greta = self.engine.npcs["npc_greta"]
        palate = IntelligentFoodSelector.infer_palate_preference(greta)
        self.assertEqual(palate, CulinaryPalatePreference.WHOLESOME_HEARTH_BREAD)

    def test_03_dynamic_hunger_decay_scales_on_exertion_curve(self):
        aldous = self.engine.npcs["npc_aldous"]
        sleep_decay = aldous.calculate_hunger_decay(current_action="SLEEP_REST")
        idle_decay = aldous.calculate_hunger_decay(current_action="IDLE")
        work_decay = aldous.calculate_hunger_decay(current_action="LABOR_WORK")
        heavy_decay = aldous.calculate_hunger_decay(current_action="SMELT_INGOTS")

        self.assertLessEqual(sleep_decay, 0.025)
        self.assertGreater(idle_decay, sleep_decay)
        self.assertGreater(work_decay, idle_decay)
        self.assertGreater(heavy_decay, work_decay)

    def test_04_proportional_income_tax_and_zero_earnings_protection(self):
        aldous = self.engine.npcs["npc_aldous"]
        tax_eng: MunicipalTaxEngine = self.engine.context.get_service("tax_engine")
        self.assertIsNotNone(tax_eng)

        aldous._unassessed_earnings_gold = 0.0
        rec_zero = tax_eng.assess_taxpayer(aldous, None, self.engine.context, current_tick=100)
        self.assertIsNone(rec_zero)

        aldous._unassessed_earnings_gold = 50.0
        rec_earned = tax_eng.assess_taxpayer(aldous, None, self.engine.context, current_tick=200)
        self.assertIsNotNone(rec_earned)
        self.assertGreater(rec_earned.tax_paid_gold, 0.0)

    def test_05_elastic_tax_evasion_by_criminals(self):
        tobias = self.engine.npcs["npc_tobias"]
        aldous = self.engine.npcs["npc_aldous"]
        t_tobias = MunicipalTaxEngine.calculate_elastic_truthfulness(tobias, None, self.engine.context)
        t_aldous = MunicipalTaxEngine.calculate_elastic_truthfulness(aldous, None, self.engine.context)
        self.assertLess(t_tobias, t_aldous)

    def test_06_municipal_indigent_legal_aid_retainer(self):
        court_eng: CourtroomLawsuitEngine = self.engine.context.get_service("courtroom_lawsuit_engine")
        self.assertIsNotNone(court_eng)
        aldous = self.engine.npcs["npc_aldous"]
        silas = self.engine.npcs["npc_silas"]

        aldous.wealth = 2.0  # Indigent
        res = court_eng.file_lawsuit(aldous, silas, "SLANDER_AND_DEFAMATION", evidence_score=50.0, context=self.engine.context, current_tick=100)
        self.assertTrue(res["success"])
        self.assertTrue(res["indigent_legal_aid"])

if __name__ == "__main__":
    unittest.main()
