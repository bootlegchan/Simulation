"""
Unit Test Suite 88: Environmental Shelter Exposure, Criminal Probation & Mindspace Grounding.
Verifies the 4 critical realism & decision-making fixes:
1. Outdoor shelter exposure penalty on sleep and continuous cold stress.
2. Grounded romance mindspace: no phantom lover daydreaming for unattached singles.
3. Criminal record & civic employment blacklisting during watch probation.
4. Notice board reading cooldown and epistemic memory de-duplication.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.behaviours.actions import ActionRegistry
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingCategory, JobPostingStatus
from src.society.courtroom_lawsuits import CourtroomLawsuitEngine
from src.society.epistemic_engine import EpistemicEngine, EpistemicStatus, VisibilityTier
from src.ai.attentional_mindspace import AttentionalMindspaceEngine


class TestEnvironmentalExposureProbationAndDeduplication(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=2026)
        self.engine.start()

        self.job_eng: DynamicJobPostingEngine = self.engine.context.get_service("job_posting_engine")
        self.court_eng: CourtroomLawsuitEngine = self.engine.context.get_service("courtroom_lawsuit_engine")
        self.ep_eng: EpistemicEngine = self.engine.context.get_service("epistemic_engine")
        self.mind_eng: AttentionalMindspaceEngine = self.engine.context.get_service("attentional_mindspace_engine")

    def test_01_outdoor_sleep_exposure_penalties(self):
        """Verify that sleeping outdoors on stone pavers inflicts energy gain penalty and stress."""
        # 1. Indoor sleeper in bedroom
        indoor_sleeper = self.engine.npcs["npc_aldous"]
        indoor_sleeper.location_id = "room_farmhouse_bedroom"
        indoor_sleeper.needs["energy"] = 40.0
        indoor_sleeper.feelings["stress"] = 20.0
        indoor_sleeper.feelings["contentment"] = 50.0

        ActionRegistry.sleep(indoor_sleeper, context=self.engine.context)
        # Full energy recovery (14.0 points) and stress relief (-12.0)
        self.assertAlmostEqual(indoor_sleeper.needs["energy"], 54.0, places=1)
        self.assertLess(indoor_sleeper.feelings["stress"], 20.0)

        # 2. Outdoor sleeper in public square
        outdoor_sleeper = self.engine.npcs["npc_tobias"]
        outdoor_sleeper.location_id = "room_village_square"
        outdoor_sleeper.needs["energy"] = 40.0
        outdoor_sleeper.feelings["stress"] = 10.0
        outdoor_sleeper.feelings["contentment"] = 50.0

        ActionRegistry.sleep(outdoor_sleeper, context=self.engine.context)
        # Penalized 50% energy gain (7.0 points) and outdoor shivering stress gain
        self.assertAlmostEqual(outdoor_sleeper.needs["energy"], 47.0, places=1)
        self.assertGreater(outdoor_sleeper.feelings["stress"], 10.0)
        self.assertLess(outdoor_sleeper.feelings["contentment"], 50.0)

    def test_02_romance_mindspace_grounded_no_phantom_lover(self):
        """Verify unattached singles with no crush do NOT generate phantom lover thoughts."""
        single_rogue = self.engine.npcs["npc_tobias"]
        # Ensure no spouse or partner
        single_rogue.social_profile["spouse_id"] = None
        single_rogue.social_profile["partner_id"] = None
        single_rogue.unmet_intimacy_tension = 45.0 # Elevated tension

        candidates = self.mind_eng.generate_candidate_thoughts(single_rogue, self.engine.context, current_tick=1000)
        # No phantom "ROMANCE_AND_CRUSH" thoughts referencing non-existent partners
        rom_thoughts = [c for c in candidates if c.domain == "ROMANCE_AND_CRUSH"]
        self.assertEqual(len(rom_thoughts), 0)

        # Instead, general courtship ambition or social longing is generated
        longing_thoughts = [c for c in candidates if c.domain == "LOVE_BELONGING"]
        self.assertGreaterEqual(len(longing_thoughts), 1)
        self.assertIn("Courtship Ambition", longing_thoughts[0].title)
        self.assertIsNone(longing_thoughts[0].target_entity_id)

    def test_03_criminal_probation_and_civic_blacklisting(self):
        """Verify intercepted illicit criminals are blacklisted from official civic jobs during probation."""
        rogue = self.engine.npcs["npc_tobias"]
        rogue.wealth = 50.0

        # Post an official job
        post = self.job_eng.create_posting(
            title="Urgent: Taproom Server",
            description="Table service in tavern",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.COMMERCIAL_ASSISTANCE,
            location_id="room_village_square",
            target_work_location_id="room_tavern",
            reward_gold=6.0,
            current_tick=500
        )

        # Initially, rogue is eligible
        claimed_init = self.job_eng.claim_job_posting(post.posting_id, rogue, self.engine.context, current_tick=500)
        self.assertTrue(claimed_init["success"])

        # Intercept an illicit operation
        post_illicit = self.job_eng.create_posting(
            title="Smuggle Cask",
            description="Clandestine transit",
            channel=PostingChannel.ILLICIT,
            category=JobPostingCategory.CONTRABAND_SMUGGLING,
            location_id="room_village_square",
            target_work_location_id="room_tavern",
            reward_gold=12.0,
            current_tick=600
        )
        self.job_eng.claim_job_posting(post_illicit.posting_id, rogue, self.engine.context, current_tick=600)

        # Station sheriff to guarantee interception
        sheriff = self.engine.npcs.get("npc_citizen_16") or self.engine.npcs.get("npc_citizen_39")
        if sheriff:
            sheriff.location_id = "room_tavern"

        res_complete = self.job_eng.complete_job_posting(post_illicit.posting_id, rogue, self.engine.context, current_tick=800)
        self.assertFalse(res_complete["success"])
        self.assertTrue(res_complete["intercepted"])

        # Rogue is now on criminal probation
        self.assertGreater(rogue.criminal_probation_until_tick, 800)
        self.assertTrue(rogue.has_tag("TAG_CONVICTED_CRIMINAL"))

        # Cannot claim new official civic job during probation!
        post_civic_2 = self.job_eng.create_posting(
            title="Street Sweeping",
            description="Civic cleanup",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.PUBLIC_HEALTH_SANITATION,
            location_id="room_village_square",
            target_work_location_id="room_village_square",
            reward_gold=5.0,
            current_tick=850
        )
        eval_job = self.job_eng.evaluate_npc_job_seeking(rogue, [post_civic_2], self.engine.context)
        self.assertIsNone(eval_job)

        claim_attempt = self.job_eng.claim_job_posting(post_civic_2.posting_id, rogue, self.engine.context, current_tick=850)
        self.assertFalse(claim_attempt["success"])
        self.assertIn("probation", claim_attempt["reason"].lower())

        # Fast-forward past probation period (3 days = 4320 ticks)
        rogue.apply_continuous_decay(delta_ticks=5000, current_tick=6000)
        self.assertFalse(rogue.has_tag("TAG_CONVICTED_CRIMINAL"))

    def test_04_notice_board_reading_cooldown_and_epistemic_deduplication(self):
        """Verify notice boards enforce cooldown and epistemic memory de-duplicates identical atoms."""
        info_eng = self.engine.context.get_service("unified_information_engine")
        reader = self.engine.npcs["npc_tobias"]
        reader.location_id = "room_village_square"
        reader._last_notice_board_read_tick = -9999

        # Read 1: Reads notice board
        read_1 = info_eng.read_notice_board(reader, "room_village_square", self.engine.context, current_tick=100)
        self.assertEqual(reader._last_notice_board_read_tick, 100)

        # Read 2: Immediate re-reading within cooldown returns empty (no compulsive loop)
        read_2 = info_eng.read_notice_board(reader, "room_village_square", self.engine.context, current_tick=160)
        self.assertEqual(len(read_2), 0)

        # De-duplication check: imparting duplicate atom reinforces existing trace instead of creating new trace
        atom_a = self.ep_eng.create_atom(
            title="Duplicate Test Landmark",
            content="A well known square fountain",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT
        )
        init_traces_count = len(self.ep_eng.npc_memories.get(reader.id, {}))

        self.ep_eng.impart_knowledge(reader, atom_a, current_tick=200)
        self.assertEqual(len(self.ep_eng.npc_memories[reader.id]), init_traces_count + 1)

        # Impart identical content again under a newly created atom instance
        atom_b = self.ep_eng.create_atom(
            title="Duplicate Test Landmark",
            content="A well known square fountain",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT
        )
        self.ep_eng.impart_knowledge(reader, atom_b, current_tick=250)

        # Traces count did NOT increase; existing trace repetition count was incremented!
        self.assertEqual(len(self.ep_eng.npc_memories[reader.id]), init_traces_count + 1)
        matched_trace = self.ep_eng.npc_memories[reader.id][atom_a.atom_id]
        self.assertGreaterEqual(matched_trace.repetition_count, 2)


if __name__ == "__main__":
    unittest.main()
