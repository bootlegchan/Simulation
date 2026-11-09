"""
Unit Test Suite 89: Clergy Community Economy, Tax/Levy Exemptions, and Fallback Eradication.
Verifies:
1. Clergy Living Stipend from Parish Member Levies / Tithes (Strict Closed-Loop).
2. Vast Community Pastoral Tasks (Grief Consolation, Sacred Liturgy, Alms Distribution).
3. Clergy Immunity from External Menial Job Seeking on Notice Boards.
4. Institutional Tax & Levy Exemptions for Sacred Buildings & Clergy.
5. Eradication of Hardcoded Fallbacks (No Phantom Free Food; No Fake Socializing with Thin Air).
6. Continuous Social Need Coupling to Loneliness & Contentment Inflation Rebalancing.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.behaviours.actions import ActionRegistry
from src.economy.taxation import MunicipalTaxEngine
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingCategory
from src.ai.drive_strategies import HungerDriveStrategy, SocializeDriveStrategy
from src.entities.status_tags import StatusTag, TagScope

class TestClergyEconomyAndFallbackEradication(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

    def test_01_clergy_living_stipend_from_parish_member_tithes(self):
        """Verify priest earns living stipend directly from parish member levies/tithes, not fiat wages."""
        priest = self.engine.npcs["npc_barnaby_priest"]
        priest.wealth = 10.0
        init_priest_wealth = priest.wealth

        aid_eng = self.engine.context.get_service("fraternal_aid_engine")
        self.assertIsNotNone(aid_eng)
        self.assertIn("aid_sacred_hearth_alms", aid_eng.lodges)
        parish_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
        parish_chest.treasury_balance = 50.0
        init_chest = parish_chest.treasury_balance

        # Priest executes Sacred Service work in the chapel
        priest.location_id = "room_chapel"
        earned = ActionRegistry.work(priest, self.engine.context)
        self.assertGreater(earned, 0.0)

        # Priest was paid from the parish chest
        self.assertGreater(priest.wealth, init_priest_wealth)
        self.assertLess(parish_chest.treasury_balance, init_chest)
        self.assertEqual(round(init_chest - parish_chest.treasury_balance, 2), round(priest.wealth - init_priest_wealth, 2))

        # Recorded pastoral community care bio log
        last_log = priest.biographical_log[-1]
        self.assertEqual(last_log["category"], "PASTORAL_COMMUNITY_CARE")
        self.assertIn("parish tithes", last_log["description"])

    def test_02_clergy_vast_community_support_tasks(self):
        """Verify clergy consoles grieving parishioners, leads liturgy, and distributes parish sustenance."""
        priest = self.engine.npcs["npc_barnaby_priest"]
        parishioner = self.engine.npcs["npc_citizen_01"]

        # Parishioner is in the chapel suffering acute grief and stress
        priest.location_id = "room_chapel"
        parishioner.location_id = "room_chapel"
        parishioner.feelings["grief"] = 60.0
        parishioner.feelings["stress"] = 55.0

        aid_eng = self.engine.context.get_service("fraternal_aid_engine")
        parish_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
        parish_chest.treasury_balance = 50.0

        # Priest conducts pastoral care
        ActionRegistry.work(priest, self.engine.context)

        # Parishioner grief and stress were consoled
        self.assertLess(parishioner.feelings["grief"], 40.0)
        self.assertLess(parishioner.feelings["stress"], 40.0)

        # Parishioner received pastoral care log
        rec_log = [l for l in parishioner.biographical_log if l["category"] == "PASTORAL_CARE_RECEIVED"]
        self.assertGreaterEqual(len(rec_log), 1)

    def test_03_clergy_immune_from_external_menial_jobs(self):
        """Verify clergy never seeks or claims external menial jobs on notice boards."""
        priest = self.engine.npcs["npc_barnaby_priest"]
        priest.wealth = 2.0  # Low wealth

        jp_eng = self.engine.context.get_service("job_posting_engine")
        # Create an official tavern server posting
        post = jp_eng.create_posting(
            title="Tavern Dishwasher",
            description="Wash tankards",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.COMMERCIAL_ASSISTANCE,
            location_id="room_village_square",
            target_work_location_id="room_tavern",
            reward_gold=10.0,
            context=self.engine.context
        )

        # Job seeking evaluation rejects clergy
        eval_res = jp_eng.evaluate_npc_job_seeking(priest, [post], self.engine.context)
        self.assertIsNone(eval_res)

        # Direct claim is rejected
        claim_res = jp_eng.claim_job_posting(post.posting_id, priest, self.engine.context, current_tick=100)
        self.assertFalse(claim_res["success"])
        self.assertIn("Clergy is dedicated solely", claim_res["reason"])

    def test_04_sacred_building_and_clergy_tax_exemptions(self):
        """Verify sacred buildings and clergy are exempt from secular income tax and property upkeep levies."""
        tax_eng = MunicipalTaxEngine()
        priest = self.engine.npcs["npc_barnaby_priest"]
        priest._unassessed_earnings_gold = 100.0
        priest.wealth = 50.0

        mayor = self.engine.npcs["npc_devon"]
        # Income tax assessment returns None (exempt)
        rec = tax_eng.assess_taxpayer(priest, mayor, self.engine.context, current_tick=1440)
        self.assertIsNone(rec)
        self.assertEqual(priest.wealth, 50.0)

        # Commercial stall fees do not assess sacred buildings
        treasury = self.engine.context.municipal_treasury
        init_treasury = treasury.balance
        tax_eng.collect_commercial_stall_fees(self.engine.context, current_tick=1440)
        # Chapel priest did not pay commercial stall fees
        self.assertEqual(priest.wealth, 50.0)

    def test_05_eradication_of_phantom_food_fallback(self):
        """Verify broke NPC without food or parish alms does NOT receive arbitrary free hunger deduction."""
        citizen = self.engine.npcs["npc_citizen_09"]
        citizen.wealth = 0.0
        citizen.inventory.clear()
        citizen.location_id = "room_isolated_cell"  # Isolated with no companions or food stores
        citizen.needs["hunger"] = 70.0
        init_hunger = citizen.needs["hunger"]

        # Empty household pantry and empty parish alms box
        hh_eng = self.engine.context.get_service("household_economy_engine")
        hh = hh_eng.get_household_for_npc(citizen.id)
        if hh:
            hh.pantry_food_rations = 0.0

        aid_eng = self.engine.context.get_service("fraternal_aid_engine")
        p_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
        p_chest.treasury_balance = 0.0  # Exhausted alms

        strat = HungerDriveStrategy()
        act = strat.execute(citizen, self.engine.context, tick=500, time_iso="Tick 500", hour=12, locations={})

        self.assertEqual(act, "STARVATION_HUNGER_UNMET")
        # Hunger was NOT reduced by a magic -30.0!
        self.assertGreaterEqual(citizen.needs["hunger"], init_hunger)
        # Suffered starvation stress
        self.assertGreater(citizen.feelings["stress"], 0.0)

    def test_06_social_isolation_loneliness_coupling_and_contentment_rebalance(self):
        """Verify depleted social need continuously builds loneliness and hardship depresses contentment."""
        citizen = self.engine.npcs["npc_citizen_09"]
        citizen.needs["social"] = 5.0  # Severe social deficit
        citizen.wealth = 1.0  # Impoverished
        citizen.needs["hunger"] = 75.0  # Hungry
        citizen.feelings["loneliness"] = 0.0
        citizen.feelings["contentment"] = 60.0

        # Apply continuous decay across 1440 ticks (1 full day of social isolation)
        citizen.apply_continuous_decay(delta_ticks=1440, current_tick=1000)

        # Loneliness surged from depleted social need
        self.assertGreater(citizen.feelings["loneliness"], 5.0)
        # Contentment was pulled down by poverty, hunger, and loneliness
        self.assertLess(citizen.feelings["contentment"], 50.0)

        # Empty room socializing does not give free social satisfaction
        citizen.location_id = "room_rectory_bedroom"
        strat = SocializeDriveStrategy()
        # Ensure no other NPC is present
        for other in self.engine.npcs.values():
            if other.id != citizen.id and other.location_id == citizen.location_id:
                other.location_id = "room_village_square"

        act = strat.execute(citizen, self.engine.context, tick=1120, time_iso="Tick 1120", hour=14, locations={})
        self.assertEqual(act, "SOLITARY_REFLECTION")

if __name__ == "__main__":
    unittest.main()
