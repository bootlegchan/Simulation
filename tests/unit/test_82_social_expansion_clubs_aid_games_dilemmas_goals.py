"""
Unit Test Suite 82: Social Expansion & Community Dynamics.
Verifies the 6 expanded social pillars:
1. Social Clubs, Confraternities & Lodges (social_clubs.json)
2. Fraternal Mutual Aid & Sickness Lodges (fraternal_aid.json)
3. Leisure Contests, Games & Tavern Wagers (recreation_games.json)
4. Moral Dilemmas, Guilt & Spiritual Confession (dilemmas.json)
5. Multi-Faceted Reputation & Organic Shunning
6. Dynamic Long-Term Life Goals & Aspirational Steering (life_goals.json)
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.social_clubs import SocialClubEngine
from src.society.fraternal_aid import FraternalAidEngine
from src.society.recreation_games import RecreationGameEngine
from src.society.dilemmas_and_confession import MoralDilemmaEngine
from src.society.life_goals import LifeGoalEngine
from src.behaviours.actions import ActionRegistry

class TestSocialExpansionClubsAidGamesDilemmasGoals(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.club_eng: SocialClubEngine = self.engine.context.get_service("social_club_engine")
        self.aid_eng: FraternalAidEngine = self.engine.context.get_service("fraternal_aid_engine")
        self.game_eng: RecreationGameEngine = self.engine.context.get_service("recreation_game_engine")
        self.dil_eng: MoralDilemmaEngine = self.engine.context.get_service("moral_dilemma_engine")
        self.lg_eng: LifeGoalEngine = self.engine.context.get_service("life_goal_engine")

    def test_01_social_clubs_discovery_and_conclave(self):
        """Verify social clubs load from data, auto-discover members, and convene conclaves."""
        self.assertIsNotNone(self.club_eng)
        self.assertIn("club_craftsmen_society", self.club_eng.clubs)
        self.assertIn("club_boar_dice_circle", self.club_eng.clubs)
        self.assertIn("club_sacred_hearth_altar", self.club_eng.clubs)

        craft_club = self.club_eng.clubs["club_craftsmen_society"]
        self.assertGreaterEqual(len(craft_club.member_ids), 2)

        # Greta (Baker) and Citizen 14 (Carpenter) are members
        greta = self.engine.npcs["npc_greta"]
        greta.location_id = "room_tavern"
        member_2 = self.engine.npcs[craft_club.member_ids[1]]
        member_2.location_id = "room_tavern"

        # Advance virtual clock to evening meeting hour (19:00)
        self.engine.clock.current_tick = 780 # 06:00 + 13h = 19:00
        init_contentment = greta.get_feeling("contentment")

        res = ActionRegistry.participate_in_club(greta, "club_craftsmen_society", self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["club_id"], "club_craftsmen_society")
        self.assertGreaterEqual(res["attendees_count"], 2)

        # Greta gained morale contentment boost
        self.assertGreater(greta.get_feeling("contentment"), init_contentment)

        # Biographical log recorded
        last_log = greta.biographical_log[-1]
        self.assertEqual(last_log["category"], "CLUB_GATHERING")
        self.assertIn("Honorable Society of Master Craftsmen", last_log["description"])

    def test_02_fraternal_mutual_aid_dues_and_sickness_relief(self):
        """Verify mutual aid lodges collect dues and disburse emergency sickness relief to distressed members."""
        self.assertIsNotNone(self.aid_eng)
        self.assertIn("aid_craftsmen_benevolence", self.aid_eng.lodges)
        lodge = self.aid_eng.lodges["aid_craftsmen_benevolence"]
        init_treasury = lodge.treasury_balance

        # Member 1 pays dues (wealth >= min_wealth 15.0)
        greta = self.engine.npcs["npc_greta"]
        greta.wealth = 50.0
        init_greta_wealth = greta.wealth

        collected = self.aid_eng.collect_daily_dues(self.engine.context, current_tick=1440)
        self.assertGreater(collected, 0.0)
        self.assertGreater(lodge.treasury_balance, init_treasury)
        self.assertLess(greta.wealth, init_greta_wealth)

        # Distressed member in poverty: Citizen 14 (Carpenter) has low wealth (4.0g < 10.0g)
        carpenter = self.engine.npcs["npc_citizen_14"]
        carpenter.wealth = 4.0
        carpenter.feelings["stress"] = 40.0
        init_carp_wealth = carpenter.wealth

        relief_cases = self.aid_eng.evaluate_emergency_relief(self.engine.context, current_tick=1440)
        self.assertGreaterEqual(len(relief_cases), 1)

        # Carpenter received emergency relief payout (8.0g)
        self.assertGreater(carpenter.wealth, init_carp_wealth)
        self.assertEqual(carpenter.wealth, round(init_carp_wealth + lodge.emergency_relief_payout_gold, 2))

        # Biographical log recorded
        last_log = carpenter.biographical_log[-1]
        self.assertEqual(last_log["category"], "FRATERNAL_AID_RECEIVED")
        self.assertIn("emergency sickness & calamity benefit", last_log["description"])

    def test_03_fraternal_bereavement_benefit_on_demise(self):
        """Verify that when a lodge member passes away, the lodge disburses bereavement benefits to the spouse."""
        lodge = self.aid_eng.lodges["aid_yeoman_league"]
        aldous = self.engine.npcs["npc_aldous"]
        spouse = self.engine.npcs["npc_citizen_02"]

        # Ensure Aldous is registered in yeoman lodge and married to Citizen 02
        if aldous.id not in lodge.member_ids:
            lodge.member_ids.append(aldous.id)
        aldous.social_profile["spouse_id"] = spouse.id
        spouse.social_profile["spouse_id"] = aldous.id
        spouse.wealth = 20.0
        init_spouse_wealth = spouse.wealth

        benefit_case = self.aid_eng.disburse_bereavement_benefit(aldous, spouse, self.engine.context, current_tick=2880)
        self.assertIsNotNone(benefit_case)
        self.assertEqual(benefit_case["payout_gold"], lodge.bereavement_benefit_gold)

        # Surviving spouse received bereavement benefit
        self.assertEqual(spouse.wealth, round(init_spouse_wealth + lodge.bereavement_benefit_gold, 2))
        last_log = spouse.biographical_log[-1]
        self.assertEqual(last_log["category"], "BEREAVEMENT_AID_RECEIVED")

    def test_04_recreation_games_sigmoid_contests_and_wagers(self):
        """Verify leisure contests, attribute-derived win probabilities, and closed-loop wager transfers."""
        self.assertIsNotNone(self.game_eng)
        self.assertIn("dice_hazard", self.game_eng.games)
        self.assertIn("arm_wrestling", self.game_eng.games)
        self.assertIn("bocce_ball", self.game_eng.games)

        actor = self.engine.npcs["npc_aldous"]
        opponent = self.engine.npcs["npc_tobias"]
        actor.location_id = "room_tavern"
        opponent.location_id = "room_tavern"
        actor.wealth = 50.0
        opponent.wealth = 50.0

        # High strength for arm wrestling
        actor.physical_attributes["strength"] = 80.0
        opponent.physical_attributes["strength"] = 30.0

        res = ActionRegistry.play_recreation_game(actor, opponent, "arm_wrestling", self.engine.context, custom_wager=0.50)
        self.assertTrue(res["success"])
        self.assertEqual(res["game_name"], "Brawn & Bench Arm-Wrestling")
        self.assertEqual(res["wager_gold"], 0.50)

        # Closed-loop wager: 1 winner gained 0.50g, 1 loser lost 0.50g
        total_after = actor.wealth + opponent.wealth
        self.assertEqual(total_after, 100.0)

    def test_05_moral_dilemmas_guilt_and_chapel_confession(self):
        """Verify transgression guilt generation, spiritual confession in chapel, and companion confiding."""
        self.assertIsNotNone(self.dil_eng)
        thief = self.engine.npcs["npc_tobias"]
        priest = self.engine.npcs["npc_barnaby_priest"]

        # 1. Record theft transgression
        init_guilt = thief.get_feeling("guilt")
        rec = self.dil_eng.record_transgression(thief, "THEFT", self.engine.context, tick=100)
        self.assertGreater(thief.get_feeling("guilt"), init_guilt)
        self.assertLess(thief.social_profile["reputation_facets"]["trustworthiness"], 75.0)

        # 2. Seek spiritual confession in chapel
        thief.location_id = "room_chapel"
        priest.location_id = "room_chapel"
        thief.wealth = 10.0
        priest.wealth = 10.0

        guilt_before_confession = thief.get_feeling("guilt")
        conf_res = ActionRegistry.seek_spiritual_confession(thief, priest, self.engine.context)
        self.assertTrue(conf_res["success"])
        self.assertLess(thief.get_feeling("guilt"), guilt_before_confession)

        # Closed-loop alms donation to priest
        self.assertGreater(priest.wealth, 10.0)

        # 3. Confide in companion with high trust
        confider = self.engine.npcs["npc_aldous"]
        confidant = self.engine.npcs["npc_greta"]
        confider.feelings["guilt"] = 40.0

        op_eng = self.engine.context.get_service("directional_opinion_engine")
        op_eng.add_modifier(from_npc=confider, to_npc=confidant, mod_id="bond", desc="Deep bond", delta=70.0, tick=100)

        confide_res = ActionRegistry.confide_secret(confider, confidant, "tax evasion", self.engine.context)
        self.assertTrue(confide_res["success"])
        self.assertLess(confider.get_feeling("guilt"), 40.0)

    def test_06_multi_faceted_reputation_and_shunning(self):
        """Verify multi-faceted reputation facets and organic shunning of untrustworthy citizens."""
        rogue = self.engine.npcs["npc_tobias"]
        upright_citizen = self.engine.npcs["npc_aldous"]
        rogue.location_id = "room_tavern"
        upright_citizen.location_id = "room_tavern"

        # Demote rogue's trustworthiness below 25.0
        rogue.social_profile.setdefault("reputation_facets", {})["trustworthiness"] = 15.0

        can_play, reason = self.game_eng.evaluate_game_invitation(rogue, upright_citizen, "dice_hazard", self.engine.context)
        self.assertFalse(can_play)
        self.assertIn("shuns", reason)

    def test_07_dynamic_life_goals_and_aspirations(self):
        """Verify dynamic life goal assignment, continuous progress calculation, and milestone achievement."""
        self.assertIsNotNone(self.lg_eng)
        merchant = self.engine.npcs["npc_beatrice"]
        merchant.wealth = 400.0 # Exceeds 350.0 target
        merchant.career_statistics["career_earnings_gold"] = 300.0

        goal = self.lg_eng.get_agent_goal(merchant.id)
        self.assertIsNotNone(goal)
        self.assertEqual(goal.goal_id, "DYNASTIC_MERCHANT")

        # Check continuous progress
        progress = self.lg_eng.calculate_progress(merchant, self.engine.context)
        self.assertGreaterEqual(progress, 0.50)

        # Evaluate milestones
        achievements = self.lg_eng.evaluate_milestones(self.engine.context, current_tick=1440)
        self.assertGreaterEqual(len(achievements), 1)

        # Check biographical entry
        merchant_logs = [l for l in merchant.biographical_log if "LIFE_MILESTONE" in l["category"] or "LIFE_GOAL" in l["category"]]
        self.assertGreaterEqual(len(merchant_logs), 1)

if __name__ == "__main__":
    unittest.main()
