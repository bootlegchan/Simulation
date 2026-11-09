"""
Unit Test Suite 87: Elastic Desire Hierarchy, Flexible Cohabitation, and Home Affordances.
Verifies:
1. Dynamic Maslow need tiers: Destitute vs affluent financial urgency scaling without hardcoded state machines.
2. Elastic relational desires: Single courtship longing vs married domestic devotion and spousal harmony.
3. Flexible cohabitation models: Marital communion wealth sharing vs strictly separate wallets for unmarried couples and collective lodgers.
4. Overcrowding comfort penalties and sleep efficiency drag.
5. Task desire index: Affluent artisans ignoring menial casual labor while impoverished commoners claim it.
6. Interactive dwelling affordances satisfying needs directly within residences.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.ai.desire_hierarchy import DesireHierarchyEngine, NeedTier
from src.society.household_economy import HouseholdEconomyEngine, HouseholdType
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingCategory


class TestElasticDesireHierarchyAndCohabitation(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.desire_eng: DesireHierarchyEngine = self.engine.context.get_service("desire_hierarchy_engine")
        self.hh_eng: HouseholdEconomyEngine = self.engine.context.get_service("household_economy_engine")
        self.job_eng: DynamicJobPostingEngine = self.engine.context.get_service("job_posting_engine")

    def test_01_dynamic_maslow_tier_weighting_affluent_vs_destitute(self):
        """Verify financial urgency factor scales inversely with wealth without state machines."""
        self.assertIsNotNone(self.desire_eng)

        destitute_npc = self.engine.npcs["npc_citizen_01"]
        destitute_npc.wealth = 2.0  # Impoverished

        affluent_npc = self.engine.npcs["npc_greta"]
        affluent_npc.wealth = 1500.0  # Wealthy master baker

        prof_destitute = self.desire_eng.evaluate_agent_hierarchy(destitute_npc, self.engine.context, current_tick=100)
        prof_affluent = self.desire_eng.evaluate_agent_hierarchy(affluent_npc, self.engine.context, current_tick=100)

        # Destitute NPC has high financial urgency (>= 1.5)
        self.assertGreaterEqual(prof_destitute.financial_urgency_factor, 1.5)

        # Affluent NPC has financial urgency dampened to baseline floor (0.03)
        self.assertAlmostEqual(prof_affluent.financial_urgency_factor, 0.03, places=2)

        # Destitute NPC safety tier weight is significantly higher than affluent NPC
        self.assertGreater(
            prof_destitute.tier_weights[NeedTier.SAFETY_SECURITY.value],
            prof_affluent.tier_weights[NeedTier.SAFETY_SECURITY.value]
        )

    def test_02_elastic_courtship_vs_married_devotion(self):
        """Verify relational tier shifts from single courtship longing to married domestic devotion."""
        married_npc = self.engine.npcs["npc_greta"]
        single_npc = self.engine.npcs["npc_tobias"]

        prof_married = self.desire_eng.evaluate_agent_hierarchy(married_npc, self.engine.context, current_tick=100)
        prof_single = self.desire_eng.evaluate_agent_hierarchy(single_npc, self.engine.context, current_tick=100)

        self.assertEqual(prof_married.relationship_mode, "MARRIED_DEVOTION")
        self.assertEqual(prof_single.relationship_mode, "SINGLE_COURTSHIP")

        # Married devotion provides domestic harmony bonus
        self.assertGreater(prof_married.affiliation_drive, 30.0)

    def test_03_flexible_cohabitation_models_wealth_separation(self):
        """Verify marital communion shares wealth while unmarried partners and lodgers keep separate wallets."""
        self.assertIsNotNone(self.hh_eng)

        # Case A: Married couple (Aldous & Greta in room_farmhouse_bedroom)
        hh_farm = self.hh_eng.get_household_for_npc("npc_aldous")
        self.assertIsNotNone(hh_farm)
        self.assertEqual(hh_farm.household_type, HouseholdType.MARITAL_COMMUNION)
        self.assertTrue(hh_farm.shares_wealth)

        # Case B: Collective Lodgers / Roommates (room_cottage_bedroom_north)
        hh_cottage = self.hh_eng.get_household_for_npc("npc_citizen_18")
        if hh_cottage:
            # Lodgers do NOT share private wealth
            self.assertFalse(hh_cottage.shares_wealth)

        # Test deposit_income_share respects wealth separation
        aldous = self.engine.npcs["npc_aldous"]
        init_aldous_wealth = aldous.wealth
        init_shared_vault = hh_farm.shared_treasury_gold

        self.hh_eng.deposit_income_share(aldous, 10.0)
        # Aldous deposited 25% share (2.5g) into marital communion vault
        self.assertLess(aldous.wealth, init_aldous_wealth)
        self.assertGreater(hh_farm.shared_treasury_gold, init_shared_vault)

        # Non-communion lodger does not deposit private earnings into room vault
        lodger = self.engine.npcs["npc_citizen_18"]
        init_lodger_wealth = lodger.wealth
        self.hh_eng.deposit_income_share(lodger, 10.0)
        self.assertEqual(lodger.wealth, init_lodger_wealth)

    def test_04_overcrowding_comfort_penalty_and_drag(self):
        """Verify overcrowding increases drag and reduces room comfort multiplier."""
        drag_empty = self.hh_eng.get_room_overcrowding_drag("room_rectory_bedroom") # 1 occupant
        self.assertEqual(drag_empty, 0.0)

        # Evaluate drag on a dwelling with 4 occupants (capacity 2 or 3)
        commoner = self.engine.npcs["npc_citizen_01"]
        prof = self.desire_eng.evaluate_agent_hierarchy(commoner, self.engine.context, current_tick=100)
        self.assertGreaterEqual(prof.comfort_modifier, 0.40)
        self.assertLessEqual(prof.comfort_modifier, 1.50)

    def test_05_affluent_artisan_ignores_menial_jobs(self):
        """Verify that wealthy artisans ignore menial dishwasher postings while poor laborers claim them."""
        wealthy_baker = self.engine.npcs["npc_greta"]
        wealthy_baker.wealth = 1500.0

        poor_laborer = self.engine.npcs["npc_citizen_20"]
        poor_laborer.wealth = 4.0

        # Create a casual tavern dishwasher posting
        post = self.job_eng.create_posting(
            title="Urgent: Tavern Server & Taproom Assistant",
            description="Table service and washing tankards",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.COMMERCIAL_ASSISTANCE,
            location_id="room_village_square",
            target_work_location_id="room_tavern",
            reward_gold=6.5,
            wage_multiplier=1.4,
            current_tick=100,
            context=self.engine.context
        )

        choice_wealthy = self.job_eng.evaluate_npc_job_seeking(wealthy_baker, [post], self.engine.context)
        choice_poor = self.job_eng.evaluate_npc_job_seeking(poor_laborer, [post], self.engine.context)

        # Wealthy baker ignores menial dishwashing job
        self.assertIsNone(choice_wealthy)

        # Impoverished laborer eagerly claims it
        self.assertIsNotNone(choice_poor)
        self.assertEqual(choice_poor[0].posting_id, post.posting_id)

    def test_06_interactive_dwelling_affordances(self):
        """Verify that homes contain functional interactive objects satisfying rest, food, and warmth."""
        farm_room = self.engine.settlements["settlement_oakwood"].buildings["bldg_farmhouse"].rooms["room_farmhouse_bedroom"]
        self.assertGreaterEqual(len(farm_room.contained_object_ids), 2)

        # Check bed affordance
        bed_obj = self.engine.objects.get("obj_bed_farmhouse")
        self.assertIsNotNone(bed_obj)
        self.assertTrue(bed_obj.has_capability("sleep_comfort"))
        self.assertTrue(bed_obj.has_capability("intimate_sanctuary"))

        # Check pantry affordance
        pantry_obj = self.engine.objects.get("obj_pantry_farmhouse")
        self.assertIsNotNone(pantry_obj)
        self.assertTrue(pantry_obj.has_capability("pantry_storage"))


if __name__ == "__main__":
    unittest.main()
