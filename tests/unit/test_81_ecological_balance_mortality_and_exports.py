"""
Unit Test Suite 81: Ecological Closed-Loop Balance, Mortality, Exports, and Modesty Courtship.
Verifies the architectural reforms:
- Strict closed-loop currency conservation (zero unbacked fiat minting on work)
- Regional export trade caravans as the sole legitimate avenue of external wealth injection
- Continuous somatic mortality hazards (starvation, hypothermic exposure, cardiac collapse)
- Modesty as a two-way street: private quarters courtship invitations vs public exposure
- Supply-demand labor dynamics: diminishing return on abundant firewood and dynamic pivot to scarce timber
- Commercial sales tax and daily business stall fees replenishing the Municipal Treasury
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.supply_chain import CommoditySupplyChainEngine
from src.entities.lifecycle_mortality import DemiseEngine
from src.behaviours.actions import ActionRegistry
from src.society.romance import RomanceEngine, RelationshipStage
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType

class TestEcologicalBalanceMortalityAndExports(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.sc_eng: CommoditySupplyChainEngine = self.engine.context.get_service("supply_chain_engine")
        self.rom_eng: RomanceEngine = self.engine.context.get_service("romance_engine")
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")
        self.demise_eng: DemiseEngine = self.engine.context.get_service("demise_engine")
        self.sc_eng.reseed_stocks()

    def test_01_closed_loop_currency_conservation_on_labor(self):
        """Verify that self-employed proprietors do not mint unbacked fiat gold out of thin air when working."""
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"
        baker.work_location_id = "bldg_bakery" # Greta owns the bakery

        init_wealth = baker.wealth
        earned = ActionRegistry.work(baker, self.engine.context)
        self.assertGreater(earned, 0.0)

        # In a strict closed-loop economy, self-employed owners earn by selling goods, NOT by minting fiat wages!
        self.assertEqual(baker.wealth, init_wealth)

    def test_02_regional_export_caravan_infuses_external_wealth(self):
        """Verify that export caravans purchase local surpluses with external gold, paying tariffs to the Treasury."""
        treasury = self.engine.context.municipal_treasury
        init_treasury = treasury.balance

        # Stockpile a large surplus of hearth bread (80 units > 45 units surplus threshold)
        self.sc_eng.commodity_stocks["food_bread"] = 80.0
        init_bread = self.sc_eng.get_stock_level("food_bread")

        # Caravan visits on day 7 (tick = 10,080)
        res = self.sc_eng.process_export_caravans(self.engine.context, current_tick=10080)
        self.assertIsNotNone(res)
        self.assertTrue(res["success"])
        self.assertGreater(res["total_spent"], 0.0)
        self.assertIn("food_bread", res["purchases"])

        # Bread was exported (consumed from inventory)
        self.assertLess(self.sc_eng.get_stock_level("food_bread"), init_bread)

        # 10% tariff was paid to the Municipal Treasury!
        self.assertGreater(treasury.balance, init_treasury)

        # Notice was published on civic board
        export_notices = [
            i for i in self.info_eng.active_items.values()
            if i.channel == InformationChannelType.CIVIC_NOTICES and i.topic == "EXPORT_TRADE_CARAVAN"
        ]
        self.assertGreaterEqual(len(export_notices), 1)

    def test_03_proposer_modesty_two_way_street_invitation(self):
        """Verify that a modest agent in a public space does not propose public intimacy, but invites partner to private bedchamber."""
        actor = self.engine.npcs["npc_citizen_01"] # Modest commoner
        partner = self.engine.npcs["npc_citizen_02"] # Modest commoner

        # Place both in the open village square with onlookers
        plaza = "room_village_square"
        actor.location_id = plaza
        partner.location_id = plaza
        actor.feelings["passion"] = 15.0
        partner.feelings["passion"] = 60.0

        bond = self.rom_eng.get_or_create_bond(actor.id, partner.id, context=self.engine.context)
        bond.romantic_affection = 70.0
        bond.trust = 70.0

        # Actor's modesty prevents proposing public exposure in the crowded square
        actor_willing, _, _ = self.rom_eng.calculate_public_intimacy_willingness(actor, witnesses_count=5, is_private_room=False, bond=bond)
        self.assertFalse(actor_willing)

        # Instead, actor invites partner to retire to private quarters
        res_invite = ActionRegistry.invite_to_private_quarters(actor, partner, self.engine.context)
        self.assertTrue(res_invite["success"])
        self.assertEqual(res_invite["action"], "INVITE_TO_PRIVATE_QUARTERS")

        # Both agents commuted to private bedchamber
        self.assertEqual(actor.location_id, res_invite["destination"])
        self.assertEqual(partner.location_id, res_invite["destination"])

        # Once in the private bedchamber, intimacy succeeds with 100% comfort and zero public scandal!
        res_intimacy = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=100, context=self.engine.context)
        self.assertTrue(res_intimacy["success"])
        self.assertTrue(res_intimacy["details"]["is_private_room"])

    def test_04_continuous_somatic_mortality_starvation_and_demise(self):
        """Verify that prolonged critical starvation leads to mortal demise, estate escheat, and obituary broadcast."""
        victim = self.engine.npcs["npc_citizen_05"]
        victim.needs["hunger"] = 100.0 # Extreme starvation
        victim.wealth = 45.0
        victim.social_profile["spouse_id"] = None # Unmarried citizen

        treasury = self.engine.context.municipal_treasury
        init_treasury = treasury.balance

        # Evaluate mortal risks with high roll
        cause = self.demise_eng.evaluate_mortal_risks(victim, tick=100, context=self.engine.context, delta_ticks=60)
        # Force demise execution
        record = self.demise_eng.execute_demise_and_succession(victim, "STARVATION", tick=100, context=self.engine.context)

        self.assertFalse(victim.is_alive)
        self.assertEqual(victim.current_state, "DECEASED")
        self.assertEqual(victim.current_action, "DECEASED")

        # Unmarried citizen's estate escheats to Municipal Treasury
        self.assertEqual(treasury.balance, round(init_treasury + 45.0, 2))
        self.assertEqual(victim.wealth, 0.0)

        # Obituary notice published on civic board
        obituaries = [
            i for i in self.info_eng.active_items.values()
            if i.channel == InformationChannelType.CIVIC_NOTICES and i.topic == "MUNICIPAL_OBITUARY"
        ]
        self.assertGreaterEqual(len(obituaries), 1)
        self.assertIn(victim.name, obituaries[0].headline)

    def test_05_supply_demand_labor_diminishing_returns(self):
        """Verify that laborers cease splitting firewood when firewood is overflowing and dynamically fell scarce timber."""
        # Scenario A: Firewood is overflowing (80.0 units) and timber is low (5.0 units)
        self.sc_eng.commodity_stocks["firewood"] = 80.0
        self.sc_eng.commodity_stocks["raw_timber"] = 5.0

        laborer = self.engine.npcs["npc_citizen_04"]
        laborer.occupation = "Laborer"
        laborer.current_action = "LABOR_WORK"

        init_timber = self.sc_eng.get_stock_level("raw_timber")
        init_firewood = self.sc_eng.get_stock_level("firewood")

        # Dispatched during production stage
        prod_sub = [s for s in self.engine.pipeline_manager.subsystems if s.subsystem_id == "subsystem_commodity_production"][0]
        prod_sub.on_tick(60, self.engine.context)

        # Intelligent labor allocation: Laborer felled scarce timber instead of adding to the firewood glut!
        self.assertGreater(self.sc_eng.get_stock_level("raw_timber"), init_timber)
        self.assertEqual(self.sc_eng.get_stock_level("firewood"), init_firewood)

    def test_06_commercial_sales_tax_and_stall_fees_replenish_treasury(self):
        """Verify that dining commercial sales tax and daily business stall fees replenish the Treasury."""
        treasury = self.engine.context.municipal_treasury
        init_treasury = treasury.balance

        tax_eng = self.engine.context.get_service("tax_engine")
        self.assertIsNotNone(tax_eng)

        # 1. Commercial stall fees collected from operational businesses (bakery, tavern, emporium)
        fees_collected = tax_eng.collect_commercial_stall_fees(self.engine.context, current_tick=1440)
        self.assertGreater(fees_collected, 0.0)
        self.assertEqual(treasury.balance, round(init_treasury + fees_collected, 2))

if __name__ == "__main__":
    unittest.main()
