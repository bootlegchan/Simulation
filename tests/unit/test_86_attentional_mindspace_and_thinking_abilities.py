"""
Unit Test Suite 86: Attentional Mindspace, Thought Weighting & Configurable Thinking Abilities.
Verifies:
1. Declarative thinking ability profiles and custom NPC cognitive configurations.
2. Dynamic synthesis of candidate mental thoughts across somatic, vocational, and emotional streams.
3. Continuous attentional weighting modulated by state, personality, focus depth, and distractibility.
4. Conscious attentional spotlight bounded by individual working memory capacity (K items).
5. Bidirectional utility bias injection into multinomial logit drive deliberation.
6. Elastic cognitive capacity and working memory scaling with individual thinking ability profiles.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.ai.attentional_mindspace import AttentionalMindspaceEngine, ThoughtItem, ThinkingAbilityProfile
from src.ai.elastic_working_memory import ElasticWorkingMemoryEngine
from src.ai.utility import UtilityEvaluator


class TestAttentionalMindspaceAndThinkingAbilities(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.mind_eng: AttentionalMindspaceEngine = self.engine.context.get_service("attentional_mindspace_engine")
        self.wm_eng: ElasticWorkingMemoryEngine = self.engine.context.get_service("elastic_working_memory_engine")

    def test_01_thinking_ability_profiles_and_custom_configuration(self):
        """Verify thinking ability profiles load from declarative settings and support custom NPC overrides."""
        self.assertIsNotNone(self.mind_eng)
        profiles = self.mind_eng.thinking_profiles

        self.assertIn("SCHOLAR_ANALYTICAL", profiles)
        self.assertIn("FOCUSED_CRAFTSMAN", profiles)
        self.assertIn("BALANCED_COMMONER", profiles)
        self.assertIn("INTUITIVE_IMPULSIVE", profiles)
        self.assertIn("SCATTERBRAIN_ABSENTMINDED", profiles)

        scholar_def = profiles["SCHOLAR_ANALYTICAL"]
        self.assertEqual(scholar_def.working_memory_capacity, 7)
        self.assertGreater(scholar_def.focus_depth, 1.0)
        self.assertLess(scholar_def.distractibility, 0.30)

        # 1. Mayor Devon is configured as SCHOLAR_ANALYTICAL
        devon = self.engine.npcs["npc_devon"]
        prof_devon = self.mind_eng.resolve_thinking_profile(devon)
        self.assertEqual(prof_devon.profile_id, "SCHOLAR_ANALYTICAL")
        self.assertEqual(prof_devon.working_memory_capacity, 7)
        self.assertGreaterEqual(prof_devon.deliberation_bandwidth, 1.25)

        # 2. Aldous Miller is configured as FOCUSED_CRAFTSMAN
        aldous = self.engine.npcs["npc_aldous"]
        prof_aldous = self.mind_eng.resolve_thinking_profile(aldous)
        self.assertEqual(prof_aldous.profile_id, "FOCUSED_CRAFTSMAN")
        self.assertEqual(prof_aldous.working_memory_capacity, 5)

        # 3. Tobias is configured as INTUITIVE_IMPULSIVE
        tobias = self.engine.npcs["npc_tobias"]
        prof_tobias = self.mind_eng.resolve_thinking_profile(tobias)
        self.assertEqual(prof_tobias.profile_id, "INTUITIVE_IMPULSIVE")
        self.assertEqual(prof_tobias.working_memory_capacity, 3)
        self.assertGreater(prof_tobias.distractibility, 0.70)

        # 4. Custom NPC override on cognition: dynamic custom capacity
        test_npc = self.engine.npcs["npc_citizen_02"]
        test_npc.cognition = {
            "thinking_profile": "SCHOLAR_ANALYTICAL",
            "working_memory_capacity": 6,
            "distractibility": 0.20
        }
        prof_custom = self.mind_eng.resolve_thinking_profile(test_npc)
        self.assertEqual(prof_custom.working_memory_capacity, 6)
        self.assertEqual(prof_custom.distractibility, 0.20)

    def test_02_dynamic_thought_synthesis_and_domain_categorization(self):
        """Verify candidate thoughts are generated dynamically across somatic, vocational, and emotional streams."""
        baker = self.engine.npcs["npc_greta"]
        baker.needs["hunger"] = 45.0  # Appreciable hunger
        baker.needs["energy"] = 90.0  # Rested
        baker.feelings["passion"] = 40.0  # Romantic interest
        baker.unmet_intimacy_tension = 35.0

        candidates = self.mind_eng.generate_candidate_thoughts(baker, self.engine.context, current_tick=780)
        domains = [c.domain for c in candidates]

        # All key active streams are represented
        self.assertIn("SOMATIC_APPETITE", domains)
        self.assertIn("VOCATIONAL_LABOR", domains)
        self.assertIn("ROMANCE_AND_CRUSH", domains)

        # Romantic thought properly identified spouse
        rom_thought = next(c for c in candidates if c.domain == "ROMANCE_AND_CRUSH")
        self.assertIn("Aldous", rom_thought.title)
        self.assertEqual(rom_thought.target_entity_id, "npc_aldous")

    def test_03_continuous_attentional_weighting_by_state_and_personality(self):
        """Verify that attentional weights scale continuously with somatic urgency, passion, and personality."""
        farmer = self.engine.npcs["npc_aldous"]

        # Case A: Well-fed, rested, on duty -> Vocational focus dominates
        farmer.needs["hunger"] = 10.0
        farmer.needs["energy"] = 95.0
        farmer.feelings["passion"] = 10.0
        farmer.unmet_intimacy_tension = 5.0
        farmer.personality["conscientiousness"] = 0.85

        res_calm = self.mind_eng.evaluate_attentional_mindspace(farmer, self.engine.context, current_tick=540) # 09:00 morning shift
        dom_calm = res_calm["dominant_thought"]
        self.assertEqual(dom_calm["domain"], "VOCATIONAL_LABOR")
        self.assertGreater(dom_calm["attentional_score"], 0.50)

        # Case B: Acute starvation -> Somatic appetite overwhelms vocational concentration
        farmer.needs["hunger"] = 80.0
        res_starving = self.mind_eng.evaluate_attentional_mindspace(farmer, self.engine.context, current_tick=540)
        dom_starving = res_starving["dominant_thought"]
        self.assertEqual(dom_starving["domain"], "SOMATIC_APPETITE")
        self.assertGreater(dom_starving["attentional_score"], 0.85)
        self.assertGreater(dom_starving["attentional_score"], dom_calm["attentional_score"])

        # Case C: Overwhelming romantic passion -> Crush thought hijacks mental spotlight
        farmer.needs["hunger"] = 15.0
        farmer.feelings["passion"] = 85.0
        farmer.unmet_intimacy_tension = 60.0
        res_passionate = self.mind_eng.evaluate_attentional_mindspace(farmer, self.engine.context, current_tick=1140) # 19:00 evening
        dom_passionate = res_passionate["dominant_thought"]
        self.assertEqual(dom_passionate["domain"], "ROMANCE_AND_CRUSH")
        self.assertIn("Greta", dom_passionate["title"])

    def test_04_attentional_spotlight_bounded_by_working_memory_capacity(self):
        """Verify that conscious attentional spotlight is strictly bounded by individual working memory capacity."""
        # 1. Scholar (Devon, capacity 7)
        devon = self.engine.npcs["npc_devon"]
        res_devon = self.mind_eng.evaluate_attentional_mindspace(devon, self.engine.context, current_tick=600)
        self.assertLessEqual(len(res_devon["spotlight_thoughts"]), 7)

        # 2. Scatterbrain (Citizen 01, capacity 2)
        scatter = self.engine.npcs["npc_citizen_01"]
        res_scatter = self.mind_eng.evaluate_attentional_mindspace(scatter, self.engine.context, current_tick=600)
        self.assertLessEqual(len(res_scatter["spotlight_thoughts"]), 2)
        self.assertEqual(len(scatter.active_thoughts), len(res_scatter["spotlight_thoughts"]))

        # 3. Dominant thought is recorded in NPC's thought history
        self.assertIsNotNone(scatter.dominant_thought)
        self.assertGreaterEqual(len(scatter.thought_history), 1)
        last_thought = scatter.thought_history[-1]
        self.assertEqual(last_thought["domain"], scatter.dominant_thought["domain"])

    def test_05_bidirectional_utility_bias_injection_into_decision_evaluator(self):
        """Verify that active conscious thoughts inject continuous utility biases into multinomial logit evaluation."""
        baker = self.engine.npcs["npc_greta"]
        baker.needs["hunger"] = 10.0
        baker.needs["energy"] = 90.0
        baker.feelings["passion"] = 10.0
        baker.personality["conscientiousness"] = 0.70

        # Baseline utilities with no attentional biases
        u_base = UtilityEvaluator.evaluate_drives(baker.needs, baker.personality)

        # Evaluate mindspace when craving food
        baker.needs["hunger"] = 65.0
        mind_eval = self.mind_eng.evaluate_attentional_mindspace(baker, self.engine.context, current_tick=720)
        biases = mind_eval["utility_biases"]
        self.assertGreater(biases.get("satisfy_hunger", 0.0), 0.0)

        # Utilities evaluated with attentional biases
        u_biased = UtilityEvaluator.evaluate_drives(
            baker.needs, baker.personality, attentional_biases=biases
        )
        self.assertGreater(u_biased["satisfy_hunger"], u_base["satisfy_hunger"])

        # When romance dominates, socialize utility is boosted while work utility is dampened
        baker.needs["hunger"] = 10.0
        baker.feelings["passion"] = 80.0
        baker.unmet_intimacy_tension = 50.0
        mind_eval_rom = self.mind_eng.evaluate_attentional_mindspace(baker, self.engine.context, current_tick=1140)
        biases_rom = mind_eval_rom["utility_biases"]

        u_rom = UtilityEvaluator.evaluate_drives(
            baker.needs, baker.personality, attentional_biases=biases_rom
        )
        self.assertGreater(u_rom["socialize"], u_base["socialize"])
        self.assertLess(u_rom["work_production"], u_base["work_production"])

    def test_06_cognitive_load_bandwidth_scales_with_individual_thinking_ability(self):
        """Verify ElasticWorkingMemoryEngine scales capacity and available slots with individual thinking ability."""
        # Scholar (Devon): base capacity ~78.0, base slots 7
        devon = self.engine.npcs["npc_devon"]
        prof_devon = self.wm_eng.get_or_create_profile(devon)
        self.assertEqual(prof_devon.base_slots, 7)
        self.assertGreaterEqual(prof_devon.base_capacity, 75.0)

        # Scatterbrain (Citizen 01): base capacity ~42.0, base slots 2
        scatter = self.engine.npcs["npc_citizen_01"]
        prof_scatter = self.wm_eng.get_or_create_profile(scatter)
        self.assertEqual(prof_scatter.base_slots, 2)
        self.assertLessEqual(prof_scatter.base_capacity, 45.0)

        # Under acute stress (stress = 80.0), available slots gracefully contract
        scatter.feelings["stress"] = 80.0
        live_scatter = self.wm_eng.evaluate_live_bandwidth(scatter, current_tick=100)
        self.assertLessEqual(live_scatter.available_slots, 2)
        self.assertGreaterEqual(live_scatter.available_slots, 1)


if __name__ == "__main__":
    unittest.main()
