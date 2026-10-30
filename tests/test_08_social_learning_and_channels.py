"""
Test Suite for Social Information Channels, Epistemic World Learning, and Need/Desire Impacts.
"""
import unittest
from src.core.path_utils import get_default_data_dir
from src.core.randomness import SeededRandom
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.npc.memory import MemorySystem
from src.society.relationships import SocialNetwork
from src.society.information_channels import (
    NoticeBoardEngine,
    WorkplaceChatterEngine,
    TavernSocialGatheringEngine,
    EpistemicBeliefEngine,
)

class TestSocialLearningAndChannels(unittest.TestCase):
    """Test suite verifying multi-channel social learning, belief reinforcement, and need/desire impacts."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=2026)
        self.random_gen = SeededRandom(seed=2026)
        self.social_net = SocialNetwork()

    def test_01_notice_board_bulletins_and_reading(self):
        """Verify posting bulletins, reading notice boards, 100% objective credibility, and need impacts."""
        notice_engine = NoticeBoardEngine()
        board_obj = InteractiveObject("obj_village_board", "Village Notice Board", capabilities=["notice_board"], location_id="room_village_square")

        # Post a criminal warrant bulletin
        bulletin = notice_engine.post_bulletin(
            board_id=board_obj.id,
            topic_category="CRIMINAL_WARRANT",
            title="WANTED: Tobias Smuggler for Burglary",
            content_payload={"suspect_id": "npc_tobias", "reward_gold": 50.0},
            posted_by_id="npc_roderick",
            posted_tick=10,
            importance_score=80.0
        )

        aldous = self.engine.npcs["npc_aldous"]
        aldous_mem = MemorySystem()

        # Aldous reads the notice board
        read_res = notice_engine.read_notice_board(aldous, board_obj, aldous_mem, current_tick=12)

        self.assertEqual(read_res["unread_count"], 1)
        self.assertIn("WANTED: Tobias Smuggler for Burglary", read_res["learned_bulletins"])

        # Check semantic belief
        fact_key = f"notice:CRIMINAL_WARRANT:{bulletin.bulletin_id}"
        self.assertIn(fact_key, aldous_mem.semantic_beliefs)
        belief = aldous_mem.semantic_beliefs[fact_key]
        self.assertEqual(belief.confidence_score, 1.0)
        self.assertEqual(belief.source_attribution, "notice_board:obj_village_board")

        # Check vigilance need impact
        self.assertGreater(aldous.needs.get("vigilance", 0.0), 0.0)

    def test_02_workplace_professional_chatter(self):
        """Verify co-located worker chatter, trade knowledge sharing, 85% credibility, and social need satisfaction."""
        eamon = self.engine.npcs["npc_aldous"]  # Farmer
        felix = self.engine.npcs["npc_beatrice"] # Merchant
        eamon.occupation = "Blacksmith"
        felix.occupation = "Blacksmith"

        eamon_mem = MemorySystem()
        felix_mem = MemorySystem()
        mems = {eamon.id: eamon_mem, felix.id: felix_mem}

        initial_social_eamon = eamon.needs.get("social", 50.0)

        chatter_res = WorkplaceChatterEngine.process_workplace_chatter(
            workers=[eamon, felix],
            work_location_id="room_smithy_forge",
            memory_systems=mems,
            current_tick=50
        )

        self.assertTrue(chatter_res["chatter_occurred"])
        self.assertEqual(chatter_res["exchanges_count"], 1)

        # Verify semantic belief learned with 0.85 credibility
        fact_key = "workplace_fact:trade_technique:blacksmith"
        self.assertIn(fact_key, eamon_mem.semantic_beliefs)
        self.assertEqual(eamon_mem.semantic_beliefs[fact_key].confidence_score, 0.85)
        self.assertEqual(eamon_mem.semantic_beliefs[fact_key].source_attribution, f"workplace_chatter:{felix.id}")

        # Verify social need increase
        self.assertGreater(eamon.needs["social"], initial_social_eamon)

    def test_03_tavern_social_gathering(self):
        """Verify tavern leisure encounters, rumor sharing, stress reduction (-25), and high social satisfaction (+35)."""
        silas = self.engine.npcs["npc_aldous"]
        greta = self.engine.npcs["npc_beatrice"]

        silas_mem = MemorySystem()
        greta_mem = MemorySystem()
        mems = {silas.id: silas_mem, greta.id: greta_mem}

        silas.needs["social"] = 20.0
        silas.needs["stress"] = 60.0

        gathering_res = TavernSocialGatheringEngine.process_tavern_gathering(
            patrons=[silas, greta],
            location_id="room_tavern_bar",
            memory_systems=mems,
            social_network=self.social_net,
            current_tick=100,
            random_gen=self.random_gen
        )

        self.assertTrue(gathering_res["gathering_occurred"])
        self.assertEqual(gathering_res["patrons_count"], 2)

        # Verify high social need boost (+35) and stress reduction (-25)
        self.assertEqual(silas.needs["social"], 55.0)
        self.assertEqual(silas.needs["stress"], 35.0)

    def test_04_epistemic_belief_reinforcement(self):
        """Verify multi-source confirmation boosts belief confidence to 1.0 and increases conviction drive."""
        aldous = self.engine.npcs["npc_aldous"]
        aldous_mem = MemorySystem()

        # Fact confirmed from notice board
        aldous_mem.update_semantic_belief(
            fact_key="scarcity_warning:wheat",
            knowledge_payload={"commodity": "wheat", "reason": "drought"},
            confidence_score=0.7,
            source_attribution="notice_board:obj_board",
            current_tick=10
        )

        # Same fact confirmed from tavern gossip
        aldous_mem.update_semantic_belief(
            fact_key="scarcity_warning:wheat_gossip",
            knowledge_payload={"commodity": "wheat", "reason": "drought"},
            confidence_score=0.6,
            source_attribution="tavern_gossip:npc_silas",
            current_tick=20
        )

        # Synthesize multi-source belief
        synth_res = EpistemicBeliefEngine.synthesize_and_reinforce_beliefs(aldous, aldous_mem)

        self.assertEqual(synth_res["reinforced_topics_count"], 1)
        self.assertIn("scarcity_warning", synth_res["reinforced_topics"])

        # Confidence boosted to 1.0
        self.assertEqual(aldous_mem.semantic_beliefs["scarcity_warning:wheat"].confidence_score, 1.0)
        self.assertGreater(aldous.needs.get("conviction", 0.0), 0.0)

if __name__ == "__main__":
    unittest.main()
