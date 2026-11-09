"""
Unit Test Suite 80: Supply Chain Self-Completion & Priority Urgency Subcontracting.
Verifies the non-FSM continuous supply chain integration:
- Continuous urgency calculation scaling with stock deficits
- Dynamic pay and duration scaling based on urgency
- Artisan self-completion of upstream requirements with direct labor earnings
- Artisan subcontracting via priority job postings with scaled compensation and tighter deadlines
- Closed-loop fulfillment and payment between employer and hired worker
- Continuous utility trade-offs between frugality/competence and wealth/fatigue
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.supply_chain import CommoditySupplyChainEngine
from src.economy.job_postings import (
    DynamicJobPostingEngine,
    PostingChannel,
    JobPostingCategory,
    JobPostingStatus,
)
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType

class TestSupplyChainSelfCompletionAndUrgencyPostings(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.sc_eng: CommoditySupplyChainEngine = self.engine.context.get_service("supply_chain_engine")
        self.job_eng: DynamicJobPostingEngine = self.engine.context.get_service("job_posting_engine")
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")
        self.sc_eng.reseed_stocks()

    def test_01_continuous_supply_urgency_calculation(self):
        """Verify continuous urgency calculation across stock deficit levels."""
        # 1. Healthy stock at or above threshold -> urgency is 0.0
        self.sc_eng.commodity_stocks["flour"] = 25.0
        urg_healthy = self.sc_eng.calculate_supply_urgency("flour", threshold_stock=20.0)
        self.assertEqual(urg_healthy, 0.0)

        # 2. Deficit halfway (10.0 / 20.0) -> moderate urgency
        self.sc_eng.commodity_stocks["flour"] = 10.0
        urg_half = self.sc_eng.calculate_supply_urgency("flour", threshold_stock=20.0)
        self.assertGreater(urg_half, 0.30)
        self.assertLess(urg_half, 0.60)

        # 3. Completely empty (0.0 / 20.0) -> maximum urgency (1.0)
        self.sc_eng.commodity_stocks["flour"] = 0.0
        urg_empty = self.sc_eng.calculate_supply_urgency("flour", threshold_stock=20.0)
        self.assertEqual(urg_empty, 1.0)

    def test_02_urgency_scaled_compensation_and_duration(self):
        """Verify that high urgency scales wage multiplier, reward, priority up and duration down."""
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"

        # Case A: Minor shortage (9.0 flour out of 10.0 threshold) -> mild urgency
        self.sc_eng.commodity_stocks["flour"] = 9.0
        reqs_mild = self.sc_eng.evaluate_artisan_supply_requirements(baker, self.engine.context, current_tick=100)
        self.assertEqual(len(reqs_mild), 1)
        mild = reqs_mild[0]
        self.assertLess(mild["urgency"], 0.20)
        self.assertLessEqual(mild["scaled_wage_multiplier"], 1.15)
        self.assertGreaterEqual(mild["scaled_duration_ticks"], 200)

        # Case B: Critical shortage (0.0 flour out of 10.0 threshold) -> maximum urgency (1.0)
        self.sc_eng.commodity_stocks["flour"] = 0.0
        reqs_crit = self.sc_eng.evaluate_artisan_supply_requirements(baker, self.engine.context, current_tick=100)
        self.assertEqual(len(reqs_crit), 1)
        crit = reqs_crit[0]
        self.assertEqual(crit["urgency"], 1.0)
        # Scaled multiplier reaches boost ceiling (1.75)
        self.assertEqual(crit["scaled_wage_multiplier"], 1.75)
        # Reward scaled up by 50%
        self.assertGreater(crit["scaled_reward_gold"], mild["scaled_reward_gold"])
        # Priority score reaches maximum tier
        self.assertEqual(crit["scaled_priority_score"], 3.5)
        # Completion duration scaled down for urgent turnaround
        self.assertEqual(crit["scaled_duration_ticks"], 120)

    def test_03_self_completion_direct_earnings_and_output(self):
        """Verify artisan personally completes upstream requirement, earning labor wages and depositing outputs."""
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"
        baker.wealth = 20.0
        baker.needs["energy"] = 90.0 # High stamina
        baker.skills["farming"] = 65.0 # Competent at milling

        # Flour is empty, but grain wheat is available
        self.sc_eng.commodity_stocks["flour"] = 0.0
        self.sc_eng.commodity_stocks["raw_wheat"] = 20.0

        init_wealth = baker.wealth
        init_earnings = baker.career_statistics.get("career_earnings_gold", 0.0)

        reqs = self.sc_eng.evaluate_artisan_supply_requirements(baker, self.engine.context, current_tick=100)
        self.assertEqual(len(reqs), 1)

        # Execute self-completion
        res = self.sc_eng.resolve_artisan_supply_choice(
            baker, reqs[0], self.engine.context, current_tick=100, force_choice="SELF_COMPLETE"
        )
        self.assertEqual(res["action"], "SELF_COMPLETE")
        self.assertTrue(res["success"])
        self.assertGreater(res["earned_gold"], 0.0)

        # Flour was produced (+2.0) and raw wheat consumed (-1.0)
        self.assertEqual(self.sc_eng.get_stock_level("flour"), 2.0)
        self.assertEqual(self.sc_eng.get_stock_level("raw_wheat"), 19.0)

        # Baker directly benefited from the work value
        self.assertGreater(baker.wealth, init_wealth)
        self.assertGreater(baker.career_statistics["career_earnings_gold"], init_earnings)

        # Biographical log recorded
        last_log = baker.biographical_log[-1]
        self.assertEqual(last_log["category"], "SUPPLY_CHAIN_SELF_COMPLETION")
        self.assertIn("flour", last_log["description"])

    def test_04_subcontracting_priority_job_posting(self):
        """Verify artisan places a priority subcontracting requisition with scaled pay and tighter duration."""
        blacksmith = self.engine.npcs["npc_aldous"]
        blacksmith.occupation = "Master Blacksmith"
        blacksmith.wealth = 150.0 # Wealthy employer
        blacksmith.needs["energy"] = 30.0 # Fatigued
        blacksmith.skills["smithing"] = 30.0 # Poor smelting competence

        # Iron ingots depleted (0.0 / 8.0 threshold), but ore is available
        self.sc_eng.commodity_stocks["iron_ingot"] = 0.0
        self.sc_eng.commodity_stocks["raw_iron_ore"] = 25.0

        reqs = self.sc_eng.evaluate_artisan_supply_requirements(blacksmith, self.engine.context, current_tick=150)
        self.assertGreaterEqual(len(reqs), 1)
        ingot_req = next(r for r in reqs if r["commodity"] == "iron_ingot")

        # Artisan subcontracts via job posting
        res = self.sc_eng.resolve_artisan_supply_choice(
            blacksmith, ingot_req, self.engine.context, current_tick=150, force_choice="POST_JOB"
        )
        self.assertEqual(res["action"], "POST_JOB")
        self.assertTrue(res["success"])

        # Verify job posting properties
        post_id = res["posting_id"]
        post = self.job_eng.active_postings[post_id]

        self.assertEqual(post.category, JobPostingCategory.SUPPLY_CHAIN_REQUISITION)
        self.assertEqual(post.employer_id, blacksmith.id)
        self.assertEqual(post.required_commodity, "iron_ingot")
        self.assertEqual(post.recipe_id, "smelt_iron")
        self.assertIn("Urgent Priority", post.title)
        self.assertEqual(post.wage_multiplier, 1.75) # Max urgency surge
        self.assertEqual(post.priority_score, 3.5) # Max priority on notice board
        self.assertEqual(post.duration_ticks, 120) # Tight turnaround deadline!

        # Notice was published to civic notice board
        civic_items = [
            i for i in self.info_eng.active_items.values()
            if i.channel == InformationChannelType.CIVIC_NOTICES and "REQUISITION_IRON_INGOT" in i.topic
        ]
        self.assertGreaterEqual(len(civic_items), 1)

    def test_05_subcontracting_worker_fulfillment_and_closed_loop_payment(self):
        """Verify hired worker completes requisition, produces commodity, and receives employer payout."""
        employer_smith = self.engine.npcs["npc_aldous"]
        employer_smith.occupation = "Master Blacksmith"
        employer_smith.wealth = 100.0

        hired_worker = self.engine.npcs["npc_citizen_02"]
        hired_worker.occupation = "Laborer"
        hired_worker.wealth = 10.0
        hired_worker.skills["smithing"] = 40.0

        self.sc_eng.commodity_stocks["iron_ingot"] = 0.0
        self.sc_eng.commodity_stocks["raw_iron_ore"] = 10.0

        # Post the requisition
        post = self.job_eng.create_posting(
            title="Smelting Requisition: Iron Ore Smelting for Forge",
            description="Smelt ore into ingots",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.SUPPLY_CHAIN_REQUISITION,
            location_id="room_village_square",
            target_work_location_id="room_blacksmith",
            reward_gold=8.0,
            employer_id=employer_smith.id,
            employer_name=employer_smith.name,
            wage_multiplier=1.5,
            recipe_id="smelt_iron",
            required_commodity="iron_ingot",
            current_tick=200
        )

        # Worker claims job
        self.job_eng.claim_job_posting(post.posting_id, hired_worker, self.engine.context, current_tick=200)

        # Complete job
        total_payout = post.reward_gold * post.wage_multiplier # 12.0g
        res = self.job_eng.complete_job_posting(post.posting_id, hired_worker, self.engine.context, current_tick=320)
        self.assertTrue(res["success"])

        # 1. Physical output produced: iron_ingot +1.0, raw_iron_ore -1.0
        self.assertEqual(self.sc_eng.get_stock_level("iron_ingot"), 1.0)
        self.assertEqual(self.sc_eng.get_stock_level("raw_iron_ore"), 9.0)

        # 2. Closed-loop payment: Employer paid 12.0g to worker
        self.assertEqual(employer_smith.wealth, 100.0 - 12.0)
        self.assertEqual(hired_worker.wealth, 10.0 + 12.0)

    def test_06_continuous_utility_frugal_vs_wealthy_artisan(self):
        """Verify continuous utility gradients: broke artisan favors self-completion; rich artisan favors subcontracting."""
        # Scenario A: Broke, high-stamina baker
        broke_baker = self.engine.npcs["npc_greta"]
        broke_baker.wealth = 2.0 # Broke
        broke_baker.needs["energy"] = 90.0 # High stamina
        broke_baker.skills["farming"] = 70.0 # Competent
        broke_baker.personality["conscientiousness"] = 0.8
        self.sc_eng.commodity_stocks["flour"] = 2.0
        self.sc_eng.commodity_stocks["raw_wheat"] = 20.0

        req_broke = self.sc_eng.evaluate_artisan_supply_requirements(broke_baker, self.engine.context, current_tick=100)[0]
        self.assertGreater(req_broke["prob_self_complete"], 0.70)
        self.assertEqual(req_broke["recommended_choice"], "SELF_COMPLETE")

        # Scenario B: Wealthy, exhausted baker
        wealthy_baker = self.engine.npcs["npc_greta"]
        wealthy_baker.wealth = 250.0 # Very wealthy
        wealthy_baker.needs["energy"] = 15.0 # Exhausted
        wealthy_baker.skills["farming"] = 10.0 # Hates farming
        wealthy_baker.personality["conscientiousness"] = 0.3

        req_wealthy = self.sc_eng.evaluate_artisan_supply_requirements(wealthy_baker, self.engine.context, current_tick=100)[0]
        self.assertGreater(req_wealthy["prob_subcontract"], 0.70)
        self.assertEqual(req_wealthy["recommended_choice"], "POST_JOB")

if __name__ == "__main__":
    unittest.main()
