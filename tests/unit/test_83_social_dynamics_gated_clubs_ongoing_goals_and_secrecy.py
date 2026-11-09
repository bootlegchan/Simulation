"""
Unit Test Suite 83: Advanced Social Dynamics, Gated & Secret Clubs, and Ongoing Life Goals.
Verifies:
1. Open vs. Gated Club membership policies and admission gating.
2. Temporary guest participation, trial attendance counters, and formal induction.
3. Secret club clandestine meetings and information gag order (exclusion from gossip diffusion).
4. NPC somatic state and continuous taste alignment determining gathering participation.
5. Ongoing lifelong maintenance goals (Devoted Spouse) evaluating spousal affection and strain.
6. Expanded NPC roster verifying complete vocational coverage across 64 citizens.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.social_clubs import SocialClubEngine
from src.society.life_goals import LifeGoalEngine
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType
from src.behaviours.actions import ActionRegistry

class TestAdvancedSocialDynamicsAndOngoingGoals(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.club_eng: SocialClubEngine = self.engine.context.get_service("social_club_engine")
        self.lg_eng: LifeGoalEngine = self.engine.context.get_service("life_goal_engine")
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")

    def test_01_open_vs_gated_club_membership_policies(self):
        """Verify that open clubs admit all interested citizens while gated clubs enforce criteria."""
        self.assertIsNotNone(self.club_eng)

        open_club = self.club_eng.clubs["club_boar_dice_circle"]
        self.assertEqual(open_club.membership_policy, "OPEN")
        # Commoner citizen with zero trade skills is eligible for open gaming circle
        commoner = self.engine.npcs["npc_citizen_01"]
        self.assertTrue(open_club.is_npc_eligible(commoner))

        gated_club = self.club_eng.clubs["club_craftsmen_society"]
        self.assertEqual(gated_club.membership_policy, "GATED")
        # Commoner is NOT eligible for Master Craftsmen
        self.assertFalse(gated_club.is_npc_eligible(commoner))
        # Master Blacksmith IS eligible
        smith = self.engine.npcs["npc_citizen_12"]
        self.assertTrue(gated_club.is_npc_eligible(smith))

    def test_02_temporary_guest_participation_and_membership_induction(self):
        """Verify temporary guest attendance at club gatherings and induction after trial sessions."""
        craft_club = self.club_eng.clubs["club_craftsmen_society"]
        init_members_count = len(craft_club.member_ids)

        # Candidate is a young apprentice who is not yet a permanent member
        apprentice = self.engine.npcs.get("npc_citizen_51") or self.engine.npcs["npc_citizen_08"]
        if apprentice.id in craft_club.member_ids:
            craft_club.member_ids.remove(apprentice.id)

        # Place 2 active craftsmen and the guest in the workshop
        member_a = self.engine.npcs["npc_greta"]
        member_b = self.engine.npcs["npc_citizen_12"]
        room = "room_tavern"
        member_a.location_id = room
        member_b.location_id = room
        apprentice.location_id = room

        # Set evening meeting hour (19:00)
        self.engine.clock.current_tick = 780

        # Session 1: Apprentice attends as a GUEST
        res_1 = self.club_eng.evaluate_club_gathering("club_craftsmen_society", room, self.engine.context, current_tick=780)
        self.assertTrue(res_1["success"])
        self.assertGreaterEqual(res_1["guests_count"], 1)
        self.assertEqual(self.club_eng.trial_attendance["club_craftsmen_society"][apprentice.id], 1)
        self.assertNotIn(apprentice.id, craft_club.member_ids)

        # Session 2: Second trial gathering leads to permanent induction!
        res_2 = self.club_eng.evaluate_club_gathering("club_craftsmen_society", room, self.engine.context, current_tick=1500)
        self.assertTrue(res_2["success"])
        self.assertIn(apprentice.id, craft_club.member_ids)
        self.assertGreater(len(craft_club.member_ids), init_members_count)

        # Biographical log recorded
        last_log = apprentice.biographical_log[-1]
        self.assertEqual(last_log["category"], "CLUB_MEMBERSHIP_INDUCTED")
        self.assertIn("Honorable Society of Master Craftsmen", last_log["description"])

    def test_03_secret_club_secrecy_oath_and_gossip_filtering(self):
        """Verify that secret clubs enforce a secrecy oath and members do not share club news in gossip."""
        secret_club = self.club_eng.clubs["club_shadow_cabal"]
        self.assertTrue(secret_club.is_secret)
        self.assertTrue(secret_club.secrecy_oath)
        self.assertEqual(secret_club.membership_policy, "SECRET")

        # Rogue member
        rogue = self.engine.npcs["npc_tobias"]
        listener = self.engine.npcs["npc_aldous"]

        # Publish a secret club news item
        secret_item = self.info_eng.publish_item(
            channel=InformationChannelType.GOSSIP_AND_RUMORS,
            topic="SECRET_CLUB_CONCLAVE_MIDNIGHT",
            headline="Obsidian Veil Clandestine Assembly",
            content="Underworld leaders convened under blood oath in the cellar vault.",
            source_npc_id=rogue.id,
            payload={"is_secret": True, "club_id": "club_shadow_cabal"},
            current_tick=100
        )

        # Tobias knows the secret
        self.assertIn(secret_item.item_id, self.info_eng.npc_knowledge_ledger[rogue.id])

        # Tobias converses with Aldous
        shared = self.info_eng.share_gossip(rogue, listener, self.engine.context, current_tick=120)
        shared_ids = [i.item_id for i in shared]

        # The secret club intelligence was strictly censored by the secrecy oath!
        self.assertNotIn(secret_item.item_id, shared_ids)
        self.assertNotIn(secret_item.item_id, self.info_eng.npc_knowledge_ledger.get(listener.id, set()))

    def test_04_npc_tastes_and_state_suitability_filtering(self):
        """Verify that exhausted or mismatched NPCs decline to participate in club conclaves."""
        sacred_club = self.club_eng.clubs["club_sacred_hearth_altar"]

        # Case A: An exhausted citizen cannot join the prayer conclave
        exhausted_npc = self.engine.npcs["npc_citizen_01"]
        exhausted_npc.needs["energy"] = 10.0 # Critical exhaustion (< 15.0)
        suitable_e, score_e, reason_e = sacred_club.calculate_taste_and_state_suitability(exhausted_npc)
        self.assertFalse(suitable_e)
        self.assertIn("exhausted", reason_e)

        # Case B: An inebriated drunk citizen is turned away from the sacred altar
        drunk_npc = self.engine.npcs["npc_citizen_03"]
        drunk_npc.needs["energy"] = 80.0
        drunk_npc.vices["alcohol_dependence"] = 45.0 # Inebriated (> 15.0)
        suitable_alc, score_alc, reason_alc = sacred_club.calculate_taste_and_state_suitability(drunk_npc)
        self.assertFalse(suitable_alc)
        self.assertIn("inebriated", reason_alc)

        # Case C: A pious, rested citizen is welcomed
        pious_npc = self.engine.npcs["npc_barnaby_priest"]
        pious_npc.needs["energy"] = 80.0
        pious_npc.feelings["stress"] = 10.0
        pious_npc.vices["alcohol_dependence"] = 0.0
        suitable_ok, score_ok, _ = sacred_club.calculate_taste_and_state_suitability(pious_npc)
        self.assertTrue(suitable_ok)
        self.assertGreaterEqual(score_ok, 15.0)

    def test_05_ongoing_devoted_spouse_goal_and_strain(self):
        """Verify ongoing maintenance goal: Devoted Spouse evaluates spousal affection and handles strain."""
        aldous = self.engine.npcs["npc_aldous"]
        greta = self.engine.npcs["npc_greta"]

        # Ensure married bond
        aldous.social_profile["spouse_id"] = greta.id
        greta.social_profile["spouse_id"] = aldous.id
        self.lg_eng.agent_goals[aldous.id] = "DEVOTED_SPOUSE"

        goal = self.lg_eng.get_agent_goal(aldous.id)
        self.assertEqual(goal.goal_type, "ONGOING_MAINTENANCE")

        # Case A: Harmonious marriage (high affection 85.0, zero resentment)
        bond = self.engine.context.get_service("romance_engine").get_or_create_bond(aldous.id, greta.id, context=self.engine.context)
        bond.romantic_affection = 85.0
        greta.feelings["resentment"] = 0.0
        greta.feelings["grief"] = 0.0

        progress_healthy = self.lg_eng.calculate_progress(aldous, self.engine.context)
        self.assertGreaterEqual(progress_healthy, 0.85)

        # Maintenance cycle awards pride and sustained fulfillment
        init_pride = aldous.get_feeling("pride")
        achievements = self.lg_eng.evaluate_milestones(self.engine.context, current_tick=1440)
        self.assertGreater(aldous.get_feeling("pride"), init_pride)
        self.assertGreaterEqual(self.lg_eng.ongoing_days_maintained.get(aldous.id, 0), 1)

        # Case B: Aspirational Strain (Spousal resentment spikes to 50.0)
        greta.feelings["resentment"] = 50.0
        progress_strained = self.lg_eng.calculate_progress(aldous, self.engine.context)
        self.assertLess(progress_strained, 0.40)

        # Milestone evaluation triggers aspiration strain!
        init_stress = aldous.get_feeling("stress")
        self.lg_eng.evaluate_milestones(self.engine.context, current_tick=2880)
        self.assertGreater(aldous.get_feeling("stress"), init_stress)
        self.assertEqual(self.lg_eng.ongoing_days_maintained.get(aldous.id, 0), 0)

        # Biographical record of aspiration strain
        last_log = aldous.biographical_log[-1]
        self.assertEqual(last_log["category"], "ASPIRATION_STRAIN")
        self.assertIn("Devoted Spouse", last_log["description"])

    def test_06_expanded_npc_roster_and_vocational_completeness(self):
        """Verify that Oakwood contains 64 autonomous citizens covering all vital village roles."""
        self.assertGreaterEqual(len(self.engine.npcs), 64)

        all_occupations = {getattr(n, "occupation", "") for n in self.engine.npcs.values()}
        expected_vocations = [
            "Farmer", "Miller", "Baker", "Blacksmith", "Carpenter",
            "Town Guard", "Woodcutter", "Mason", "Weaver", "Healer",
            "Brewer", "Apprentice", "Priest", "Mayor", "Merchant"
        ]
        for voc in expected_vocations:
            self.assertTrue(
                any(voc.lower() in o.lower() for o in all_occupations),
                f"Missing vital village occupation: {voc}"
            )

if __name__ == "__main__":
    unittest.main()
