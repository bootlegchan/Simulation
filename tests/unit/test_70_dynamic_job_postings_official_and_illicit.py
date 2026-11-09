"""
Unit Test Suite 70: Dynamic Job Postings across Official & Illicit Channels.
Verifies:
  1. Dynamic generation of official postings based on civic & commercial needs (tavern rushes, infrastructure repair, watch deficit).
  2. Dynamic generation of illicit postings based on underworld needs (contraband smuggling, debt enforcement muscle, burglary lookouts).
  3. Channel separation and visibility (public notice boards vs covert underworld chalk marks).
  4. Moral filter and applicant volition: honorable citizens reject illicit postings while rogues accept them.
  5. Somatic fatigue safety: exhausted citizens (energy < 20) decline jobs to rest.
  6. Official job completion: honest compensation, career stat tracking, and proportional income tax assessment.
  7. Illicit job completion: tax-free bounties, moral erosion, and watch interception risk.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.job_postings import (
    DynamicJobPostingEngine,
    PostingChannel,
    JobPostingCategory,
    JobPostingStatus,
    JobPostingRecord,
)

class TestDynamicJobPostingsOfficialAndIllicit(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.job_eng = self.engine.context.get_service("job_posting_engine")
        self.job_eng.active_postings.clear()
        self.job_eng.posting_history.clear()

    def test_01_dynamic_official_needs_generation(self):
        """Verify that settlement commercial rushes and watch deficits generate official job postings."""
        # 1. Simulate tavern patron rush
        tavern_room = "room_tavern"
        self.engine.npcs["npc_citizen_01"].location_id = tavern_room
        self.engine.npcs["npc_citizen_02"].location_id = tavern_room
        self.engine.npcs["npc_citizen_03"].location_id = tavern_room
        self.engine.npcs["npc_citizen_04"].location_id = tavern_room
        self.engine.npcs["npc_silas"].location_id = "room_village_square" # Silas off-duty

        # Advance tick to night hours to trigger watch deficit
        self.engine.clock.current_tick = 1380 # 23:00 hour
        new_postings = self.job_eng.evaluate_settlement_needs(self.engine.context, current_tick=1380)

        official_posts = [p for p in new_postings if p.channel == PostingChannel.OFFICIAL]
        self.assertGreaterEqual(len(official_posts), 1)

        categories = [p.category for p in official_posts]
        self.assertTrue(
            JobPostingCategory.COMMERCIAL_ASSISTANCE in categories or
            JobPostingCategory.CIVIC_WATCH_PATROL in categories or
            JobPostingCategory.INFRASTRUCTURE_REPAIR in categories
        )

        first_official = official_posts[0]
        self.assertEqual(first_official.status, JobPostingStatus.OPEN)
        self.assertFalse(first_official.is_covert)
        self.assertGreater(first_official.reward_gold, 0.0)

    def test_02_dynamic_illicit_needs_generation(self):
        """Verify that underworld smugglers and defaulters trigger covert illicit job postings."""
        # Ensure a smuggler and defaulter are active
        self.engine.npcs["npc_tobias"].social_profile["has_contraband"] = True
        self.engine.npcs["npc_citizen_05"].add_status_tag(
            type("MockTag", (), {"tag_id": "TAG_KNOWN_DEFAULTER", "scope": type("S", (), {"value": "COMMERCIAL"})()})()
        )

        new_postings = self.job_eng.evaluate_settlement_needs(self.engine.context, current_tick=1400)
        illicit_posts = [p for p in new_postings if p.channel == PostingChannel.ILLICIT]
        self.assertGreaterEqual(len(illicit_posts), 1)

        first_illicit = illicit_posts[0]
        self.assertEqual(first_illicit.channel, PostingChannel.ILLICIT)
        self.assertTrue(first_illicit.is_covert)
        self.assertGreater(first_illicit.risk_tier, 0)
        self.assertGreater(first_illicit.reward_gold, 10.0) # High illicit bounty

    def test_03_moral_filter_honorable_vs_rogue_applicant(self):
        """Verify that honorable citizens reject illicit postings while criminals accept them."""
        aldous = self.engine.npcs["npc_aldous"] # Honorable farmer (Honor=0.8, CrimeProp=0)
        tobias = self.engine.npcs["npc_tobias"] # Rogue smuggler (CrimeProp=60, Honor=0.2)

        # Create both an official and an illicit job
        official_post = self.job_eng.create_posting(
            title="Farm Hand Harvest Help",
            description="Harvest grain sacks",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.AGRICULTURAL_HARVEST,
            location_id="room_village_square",
            target_work_location_id="room_farmhouse",
            reward_gold=6.0,
            current_tick=100
        )
        illicit_post = self.job_eng.create_posting(
            title="Night Contraband Run",
            description="Smuggle lockbox",
            channel=PostingChannel.ILLICIT,
            category=JobPostingCategory.CONTRABAND_SMUGGLING,
            location_id="room_underworld",
            target_work_location_id="room_cellar",
            reward_gold=20.0,
            risk_tier=2,
            current_tick=100
        )

        # Aldous evaluates both:
        eval_aldous = self.job_eng.evaluate_npc_job_seeking(aldous, [illicit_post], self.engine.context)
        # Aldous MUST reject illicit posting due to moral conscience!
        self.assertIsNone(eval_aldous)

        # Aldous evaluates official posting:
        eval_aldous_off = self.job_eng.evaluate_npc_job_seeking(aldous, [official_post], self.engine.context)
        self.assertIsNotNone(eval_aldous_off)
        self.assertEqual(eval_aldous_off[0].posting_id, official_post.posting_id)

        # Tobias evaluates illicit posting:
        eval_tobias = self.job_eng.evaluate_npc_job_seeking(tobias, [illicit_post], self.engine.context)
        self.assertIsNotNone(eval_tobias)
        self.assertEqual(eval_tobias[0].posting_id, illicit_post.posting_id)

    def test_04_somatic_fatigue_refusal(self):
        """Verify that exhausted workers (energy < 20) decline job postings to sleep/rest."""
        worker = self.engine.npcs["npc_citizen_06"]
        worker.needs["energy"] = 15.0 # Exhausted

        post = self.job_eng.create_posting(
            title="Public Works Masonry",
            description="Fix stone bridge",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.INFRASTRUCTURE_REPAIR,
            location_id="room_village_square",
            target_work_location_id="room_village_square",
            reward_gold=10.0,
            current_tick=100
        )

        eval_res = self.job_eng.evaluate_npc_job_seeking(worker, [post], self.engine.context)
        self.assertIsNone(eval_res)

    def test_05_official_job_claim_and_completion_lifecycle(self):
        """Verify that claiming and completing an official job pays honest wages and tracks taxes."""
        worker = self.engine.npcs["npc_citizen_07"]
        worker.wealth = 20.0
        worker._unassessed_earnings_gold = 0.0

        post = self.job_eng.create_posting(
            title="Infirmary Triage Assistant",
            description="Clean medicinal bowls",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.PUBLIC_HEALTH_SANITATION,
            location_id="room_village_square",
            target_work_location_id="room_village_square",
            reward_gold=12.0,
            duration_ticks=120,
            current_tick=100
        )

        claim_res = self.job_eng.claim_job_posting(post.posting_id, worker, self.engine.context, current_tick=100)
        self.assertTrue(claim_res["success"])
        self.assertEqual(post.status, JobPostingStatus.CLAIMED)
        self.assertEqual(post.assigned_worker_id, worker.id)

        # Complete job
        complete_res = self.job_eng.complete_job_posting(post.posting_id, worker, self.engine.context, current_tick=220)
        self.assertTrue(complete_res["success"])
        self.assertEqual(complete_res["status"], "COMPLETED")
        self.assertFalse(complete_res["intercepted"])

        # Verified honest payment and tax tracking
        self.assertEqual(worker.wealth, 32.0)
        self.assertEqual(worker._unassessed_earnings_gold, 12.0)
        self.assertEqual(worker.career_statistics.get("career_earnings_gold"), 12.0)
        self.assertEqual(self.job_eng.total_official_jobs_completed, 1)

    def test_06_illicit_job_completion_and_interception_risk(self):
        """Verify illicit job execution: tax-free payout, moral erosion, and watch interception."""
        rogue = self.engine.npcs["npc_tobias"]
        rogue.wealth = 15.0
        start_moral_erosion = rogue.moral_erosion

        # Case A: Successful covert job (Sheriff not present)
        post_success = self.job_eng.create_posting(
            title="Secret Dead-Drop Delivery",
            description="Deliver blackmail note",
            channel=PostingChannel.ILLICIT,
            category=JobPostingCategory.BLACKMAIL_DEAD_DROP,
            location_id="room_underworld",
            target_work_location_id="room_underworld",
            reward_gold=25.0,
            risk_tier=2,
            current_tick=300
        )
        self.job_eng.claim_job_posting(post_success.posting_id, rogue, self.engine.context, current_tick=300)

        # Force random roll high to avoid interception
        orig_random = self.engine.context.random.random
        self.engine.context.random.random = lambda: 0.99
        res_a = self.job_eng.complete_job_posting(post_success.posting_id, rogue, self.engine.context, current_tick=480)
        self.assertTrue(res_a["success"])
        self.assertFalse(res_a["intercepted"])
        self.assertEqual(rogue.wealth, 40.0) # Tax-free bounty added!
        self.assertGreater(rogue.moral_erosion, start_moral_erosion)

        # Case B: Intercepted by Watch
        post_caught = self.job_eng.create_posting(
            title="Warehouse Burglary",
            description="Break into shop",
            channel=PostingChannel.ILLICIT,
            category=JobPostingCategory.BURGLARY_LOOKOUT,
            location_id="room_underworld",
            target_work_location_id="room_village_square",
            reward_gold=20.0,
            risk_tier=3,
            current_tick=500
        )
        self.job_eng.claim_job_posting(post_caught.posting_id, rogue, self.engine.context, current_tick=500)

        # Force interception roll
        self.engine.context.random.random = lambda: 0.01
        res_b = self.job_eng.complete_job_posting(post_caught.posting_id, rogue, self.engine.context, current_tick=680)
        self.assertFalse(res_b["success"])
        self.assertTrue(res_b["intercepted"])
        self.assertEqual(res_b["status"], "INTERCEPTED")
        self.assertGreater(self.job_eng.total_illicit_intercepted, 0)

        # Restore random generator
        self.engine.context.random.random = orig_random

if __name__ == "__main__":
    unittest.main()
