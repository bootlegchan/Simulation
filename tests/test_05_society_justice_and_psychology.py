"""
Consolidated Test Suite 05: Society, Factions, Civic Governance, Interpersonal Bonds, Justice, Criminology, and Psychology.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.factions import FactionHostilityMatrix
from src.society.coalitions import CoalitionManager
from src.society.civic import MunicipalTreasury, CorruptionManager
from src.society.romance import InterpersonalBond, RelationshipStage
from src.society.status import PrestigeCalculator
from src.society.culture import FestivalManager, FestivalEvent
from src.society.underworld import CrimeSeverity, UnderworldActivityEngine
from src.society.justice import SentenceType, JudicialCourtroomEngine
from src.society.attachment_theory import AttachmentStyle, AttachmentEngine
from src.society.triangular_love import LoveTaxonomy, TriangularLoveModel
from src.society.social_penetration import DisclosureTier, SocialPenetrationEngine
from src.society.front_back_stage import GoffmanFrontBackStageEngine
from src.society.mate_retention import MateRetentionEngine
from src.society.relationships import SocialNetwork
from src.society.taboos import StigmaTracker


class TestSocietyJusticeAndPsychology(unittest.TestCase):
    """Verifies Factions, Governance, Interpersonal Bonds, Criminology, Justice System, and Interpersonal Psychology."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.social_net = SocialNetwork()

    def test_factions_coalitions_and_municipal_treasury(self):
        matrix = FactionHostilityMatrix()
        matrix.set_hostility("faction_farmers_guild", "faction_merchants_guild", 20.0)
        self.assertEqual(matrix.get_hostility("faction_farmers_guild", "faction_merchants_guild"), 20.0)

        coalition_mgr = CoalitionManager()
        coalition = coalition_mgr.form_coalition(
            coalition_id="c_trade",
            name="Trade Alliance",
            faction_ids=["faction_farmers_guild", "faction_merchants_guild"],
            hostility_matrix=matrix
        )
        self.assertIsNotNone(coalition)
        self.assertEqual(len(coalition.member_faction_ids), 2)

        treasury = MunicipalTreasury(initial_balance=500.0)
        treasury.deposit_tax(25.0)
        self.assertEqual(treasury.balance, 525.0)

        bribe_prob = CorruptionManager.calculate_bribe_success_probability(bribe_amount=50.0, official_wealth_need=50.0, anonymity=0.8)
        self.assertTrue(0.0 <= bribe_prob <= 1.0)

    def test_interpersonal_bonds_courtship_and_infidelity(self):
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]

        bond = InterpersonalBond(aldous.id, beatrice.id, physical_attraction=60.0, romantic_affection=30.0)
        courtship_ok = bond.attempt_courtship(amount=25.0)

        self.assertTrue(courtship_ok)
        self.assertEqual(bond.stage, RelationshipStage.COURTING)

        infidelity_res = bond.register_infidelity(rival_id="npc_silas")
        self.assertEqual(bond.stage, RelationshipStage.EXES)
        self.assertEqual(infidelity_res["trust"], -100.0)

    def test_prestige_social_class_and_festivals(self):
        devon_mayor = self.engine.npcs["npc_devon"]
        barnaby_beggar = self.engine.npcs["npc_barnaby_beggar"]

        prestige_devon = PrestigeCalculator.calculate_prestige(devon_mayor)
        prestige_barnaby = PrestigeCalculator.calculate_prestige(barnaby_beggar)
        self.assertGreater(prestige_devon, prestige_barnaby)

        fest_mgr = FestivalManager()
        fest_event = FestivalEvent("fest_harvest", "Harvest Gala", tick_duration=1440)
        fest_mgr.start_festival(fest_event)
        self.assertTrue(fest_mgr.is_festival_active())

    def test_criminology_spectrum_and_judicial_courtroom_trials(self):
        tobias = self.engine.npcs["npc_tobias"]
        aldous = self.engine.npcs["npc_aldous"]
        devon_magistrate = self.engine.npcs["npc_devon"]
        oswald_sheriff = self.engine.npcs["npc_oswald_guard"]

        # Level 1 Taboo
        taboo = UnderworldActivityEngine.execute_social_taboo(actor=tobias, target=aldous, taboo_type="smear_insult", social_network=self.social_net)
        self.assertEqual(taboo["severity"], CrimeSeverity.SOCIAL_TABOO.value)

        # Level 2 Petty Crime
        petty = UnderworldActivityEngine.execute_petty_crime(actor=tobias, victim=aldous, crime_type="pickpocketing", witness_ids=[oswald_sheriff.id])
        self.assertEqual(petty["severity"], CrimeSeverity.PETTY_ILLEGAL.value)

        # Courtroom Trial Execution
        court_engine = JudicialCourtroomEngine()
        warrant = court_engine.issue_arrest_warrant(petty, reporting_npc_id=aldous.id)

        trial_res = court_engine.conduct_courtroom_trial(
            warrant_id=warrant["warrant_id"],
            magistrate=devon_magistrate,
            prosecutor_sheriff=oswald_sheriff,
            accused=tobias,
            witnesses=[oswald_sheriff],
            social_network=self.social_net,
            current_tick=20
        )
        self.assertIn("is_guilty", trial_res)

        # Sentence Execution
        stigma = StigmaTracker(tobias.id)
        treasury = MunicipalTreasury()
        sent = court_engine.execute_sentence(
            trial_record=trial_res,
            accused=tobias,
            victim=aldous,
            municipal_treasury=treasury,
            stigma_tracker=stigma
        )
        self.assertTrue(sent["executed"])

    def test_interpersonal_psychology_theories(self):
        beatrice = self.engine.npcs["npc_beatrice"]
        aldous = self.engine.npcs["npc_aldous"]
        tobias = self.engine.npcs["npc_tobias"]

        # Attachment Styles
        style = AttachmentEngine.determine_attachment_style(beatrice)
        self.assertIn(style, [AttachmentStyle.SECURE, AttachmentStyle.ANXIOUS_PREOCCUPIED, AttachmentStyle.DISMISSIVE_AVOIDANT, AttachmentStyle.FEARFUL_AVOIDANT])

        # Triangular Love Model
        love = TriangularLoveModel(intimacy=80.0, passion=70.0, commitment=90.0)
        self.assertEqual(love.get_love_taxonomy(), LoveTaxonomy.CONSUMMATE_LOVE)

        # Social Penetration Onion Model
        tier = SocialPenetrationEngine.evaluate_max_disclosure_tier(trust_score=85.0, privacy_rating=90.0)
        self.assertEqual(tier, DisclosureTier.CORE_SECRETS_AND_FEARS)

        # Goffman Front/Back Stage
        front_res = GoffmanFrontBackStageEngine.adjust_behavior_for_context(tobias, privacy_rating=15.0, proposed_drive="vice_indulgence", utility_score=80.0)
        self.assertEqual(front_res["context"], "FRONT_STAGE")
        self.assertTrue(front_res["is_suppressed"])

        # Mate Retention
        retention = MateRetentionEngine.evaluate_mate_retention_urgency(aldous, suspicion_score=70.0, presence_of_rivals=True)
        self.assertGreater(retention["retention_urgency"], 50.0)


if __name__ == "__main__":
    unittest.main()
