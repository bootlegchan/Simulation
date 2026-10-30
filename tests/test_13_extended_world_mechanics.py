"""
Test Suite 13: Extended World Mechanics, Micro-Climates, Infrastructure Sanitation,
Subjective Fog-of-War Cognition, Habituation Loops, Credit Markets, Guild Cartels,
Lineage Dowries, and Celestial Superstitions.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject
from src.world.climate_and_infrastructure import MicroClimateEngine, InfrastructureSanitationEngine
from src.ai.cognitive_planning import SubjectiveCognitionEngine, HabituationEngine
from src.economy.credit_and_guilds import CreditInstrumentManager, GuildCartelManager
from src.society.lineage_and_superstitions import LineageAllianceEngine, SuperstitionOmensEngine


class TestExtendedWorldMechanics(unittest.TestCase):
    """Verifies all 8 modular extended simulation systems and their data-driven interactions."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.settlement = self.engine.settlements["settlement_oakwood"]

    def test_01_environmental_micro_climates_and_hearth_warmth(self):
        """Verify ambient calculation, indoor insulation, hearth heating, and hypothermia exposure."""
        climate = self.engine.micro_climate_engine
        self.assertIsNotNone(climate)

        # 1. Ambient winter daytime temperature
        winter_ambient = climate.calculate_ambient_temperature(season="WINTER", time_of_day="DAY")
        self.assertEqual(winter_ambient, 0.0)  # -5.0 + 5.0 = 0.0°C

        # 2. Indoor room without hearth vs with hearth
        bedroom = self.settlement.buildings["bldg_farmhouse"].rooms["room_farmhouse_bedroom"]
        kitchen = self.settlement.buildings["bldg_farmhouse"].rooms["room_farmhouse_kitchen"]

        bed_temp = climate.evaluate_room_temperature(bedroom, self.settlement.buildings["bldg_farmhouse"], winter_ambient, self.engine.objects)
        kitchen_temp = climate.evaluate_room_temperature(kitchen, self.settlement.buildings["bldg_farmhouse"], winter_ambient, self.engine.objects)

        # Kitchen has family hearth (+22°C delta)
        self.assertGreater(kitchen_temp, bed_temp)
        self.assertGreaterEqual(kitchen_temp, 25.0)

        # 3. Hypothermia physiological exposure
        aldous = self.engine.npcs["npc_aldous"]
        aldous.feelings["stress"] = 0.0
        exposure = climate.apply_exposure_effects_to_npc(aldous, room_temperature=-1.0)
        self.assertTrue(exposure["is_hypothermic"])
        self.assertGreater(aldous.get_feeling("stress"), 15.0)

    def test_02_infrastructure_water_source_decay_and_purification(self):
        """Verify water well silt accumulation, purity decay, and mineral alum purification."""
        sanitation = self.engine.sanitation_engine
        self.assertIsNotNone(sanitation)

        # 1. Register and check initial well
        well = sanitation.get_or_register_source("object_town_well", source_type="town_well")
        self.assertEqual(well["purity"], 100.0)

        # 2. Daily silt accumulation
        for tick in range(1440, 5760, 1440):
            res = sanitation.process_daily_silt_accumulation(tick)
            self.assertIn("object_town_well", res)

        self.assertLess(well["purity"], 90.0)

        # 3. Purify well with mineral alum
        aldous = self.engine.npcs["npc_aldous"]
        alum = ItemInstance("inst_alum_1", "item_purification_alum", 100.0, 100.0, 1.0, owner_id=aldous.id)
        aldous.inventory.append(alum)

        purify_res = sanitation.purify_water_source("object_town_well", aldous, purification_alum=alum, current_tick=6000)
        self.assertTrue(purify_res["success"])
        self.assertTrue(purify_res["alum_used"])
        self.assertGreater(purify_res["purity_after"], 95.0)

    def test_03_subjective_fog_of_war_cognition_and_expectation_failure(self):
        """Verify mental map staleness decay and wasted trip expectation failure."""
        cognition = self.engine.subjective_cognition_engine
        self.assertIsNotNone(cognition)

        beatrice = self.engine.npcs["npc_beatrice"]
        shop_loc = "room_vance_shop_floor"

        # 1. Record perceived bread inventory
        cognition.record_perceived_inventory(beatrice.id, shop_loc, "food_bread", quantity=5, current_tick=100)
        conf_fresh = cognition.evaluate_belief_confidence(beatrice.id, shop_loc, "food_bread", current_tick=200)
        conf_stale = cognition.evaluate_belief_confidence(beatrice.id, shop_loc, "food_bread", current_tick=10000)

        self.assertGreater(conf_fresh, conf_stale)
        self.assertLess(conf_stale, 0.4)

        # 2. Beatrice travels expecting bread, but actual stock is 0!
        beatrice.feelings["stress"] = 0.0
        mismatch_res = cognition.verify_expectation_against_reality(
            npc=beatrice,
            location_id=shop_loc,
            target_item_id="food_bread",
            actual_inventory_count=0,
            current_tick=10100
        )
        self.assertFalse(mismatch_res["matched"])
        self.assertTrue(mismatch_res["replan_recommended"])
        self.assertGreater(beatrice.get_feeling("stress"), 10.0)

    def test_04_habituation_loops_and_withdrawal(self):
        """Verify habit formation, utility boost, and missed routine withdrawal stress."""
        habit = self.engine.habituation_engine
        self.assertIsNotNone(habit)

        priest = self.engine.npcs["npc_barnaby_priest"]

        # 1. Establish strong daily worship habit
        for _ in range(12):
            habit.record_habit_execution(priest.id, "daily_worship")

        strength = habit.get_habit_strength(priest.id, "daily_worship")
        self.assertGreaterEqual(strength, 50.0)

        # 2. Check utility priority boost
        boost = habit.calculate_action_utility_boost(priest.id, "daily_worship")
        self.assertGreater(boost, 15.0)

        # 3. Missing habit triggers withdrawal stress
        priest.feelings["stress"] = 0.0
        withdrawal = habit.process_daily_habit_decay_and_withdrawal(priest)
        self.assertIn("daily_worship", withdrawal["withdrawal_habits"])
        self.assertGreater(priest.get_feeling("stress"), 15.0)

    def test_05_informal_credit_promissory_notes_and_secondary_discounting(self):
        """Verify issuing promissory notes, trading debt on secondary markets, and debt redemption."""
        credit = self.engine.credit_manager
        self.assertIsNotNone(credit)

        valeria = self.engine.npcs["npc_valeria_notary"]
        aldous = self.engine.npcs["npc_aldous"]
        bruno = self.engine.npcs["npc_bruno_scavenger"]

        # 1. Valeria issues promissory note loan to Aldous (50 gold)
        initial_aldous_wealth = aldous.wealth
        issue_res = credit.issue_promissory_note(debtor=aldous, creditor=valeria, amount=50.0, current_tick=100)
        self.assertTrue(issue_res["success"])
        self.assertEqual(aldous.wealth, initial_aldous_wealth + 50.0)

        # Valeria now possesses the promissory note item
        note_inst = next(i for i in valeria.inventory if i.item_def_id == "item_promissory_note")
        self.assertIsNotNone(note_inst)

        # 2. Valeria sells the 50g note to Marcus Vance at 80% secondary discount (40g)
        marcus = self.engine.npcs["npc_marcus_vance"]
        marcus.wealth = 200.0
        trade_res = credit.trade_secondary_debt(seller=valeria, buyer=marcus, note_instance=note_inst)
        self.assertTrue(trade_res["success"])
        self.assertEqual(trade_res["discounted_price"], 40.0)
        self.assertIn(note_inst, marcus.inventory)

        # 3. Aldous repays the debt to Marcus
        aldous.wealth = 100.0
        redeem_res = credit.redeem_debt(debtor=aldous, holder=marcus, note_instance=note_inst)
        self.assertTrue(redeem_res["success"])
        self.assertTrue(redeem_res["settled"])

    def test_06_guild_cartel_price_fixing_and_scavenger_undercutting(self):
        """Verify cartel floor prices, fining cartel members, and non-guild black market undercutting."""
        cartel = self.engine.guild_cartel_manager
        self.assertIsNotNone(cartel)

        torvald = self.engine.npcs["npc_torvald_guildmaster"]
        eamon = self.engine.npcs["npc_eamon"]
        bruno = self.engine.npcs["npc_bruno_scavenger"]

        # 1. Blacksmith Guild floor for iron_sword is 120.0
        guild = cartel.get_guild_for_item("iron_sword")
        self.assertIsNotNone(guild)
        self.assertEqual(guild["price_floors"]["iron_sword"], 120.0)

        # 2. Guild member Eamon attempts to sell for 90.0 -> Fined by guild!
        eamon.wealth = 100.0
        sale_eamon = cartel.evaluate_sale_price(seller=eamon, item_id="iron_sword", offered_price=90.0, current_tick=200)
        self.assertTrue(sale_eamon["is_restricted"])
        self.assertFalse(sale_eamon["compliant"])
        self.assertTrue(sale_eamon["is_guild_member"])
        self.assertGreater(sale_eamon["fine_levied"], 0.0)
        self.assertLess(eamon.wealth, 100.0)

        # 3. Non-guild scavenger Bruno sells iron_ingot below floor -> Black market undercut!
        sale_bruno = cartel.evaluate_sale_price(seller=bruno, item_id="iron_ingot", offered_price=20.0, current_tick=250)
        self.assertTrue(sale_bruno["is_restricted"])
        self.assertFalse(sale_bruno["compliant"])
        self.assertFalse(sale_bruno["is_guild_member"])
        self.assertTrue(sale_bruno["black_market_undercut"])

    def test_07_lineage_marriage_dowry_alliances_and_breach(self):
        """Verify inter-clan marriage contracts, dowry transfers, and blood feud on contract breach."""
        lineage = self.engine.lineage_alliance_engine
        self.assertIsNotNone(lineage)

        marcus_vance = self.engine.npcs["npc_marcus_vance"]  # Bride's father
        clara_vance = self.engine.npcs["npc_clara_vance"]    # Bride
        devon = self.engine.npcs["npc_devon"]                # Suitor's father (Mayor)
        eamon = self.engine.npcs["npc_eamon"]                # Suitor

        # 1. Draft dowry contract (100 gold dowry)
        contract_res = lineage.draft_marriage_dowry_contract(
            suitor_clan_head=devon,
            bride_clan_head=marcus_vance,
            suitor=eamon,
            bride=clara_vance,
            dowry_type="GOLD_DOWRY",
            dowry_amount=100.0,
            current_tick=500
        )
        self.assertTrue(contract_res["success"])
        contract_id = contract_res["contract_id"]

        # 2. Execute marriage alliance
        devon.wealth = 200.0
        initial_marcus_wealth = marcus_vance.wealth
        exec_res = lineage.execute_marriage_alliance(contract_id, suitor_clan_head=devon, bride_clan_head=marcus_vance)
        self.assertTrue(exec_res["success"])
        self.assertTrue(exec_res["alliance_established"])
        self.assertEqual(marcus_vance.wealth, initial_marcus_wealth + 100.0)

        # 3. Breach contract -> Feud animosity surge
        breach_res = lineage.break_marriage_contract(contract_id, violator_npc=eamon, scorned_clan_head=marcus_vance)
        self.assertTrue(breach_res["success"])
        self.assertTrue(breach_res["feud_triggered"])
        self.assertGreater(marcus_vance.get_feeling("resentment"), 50.0)

    def test_08_celestial_omens_moral_panics_and_scapegoating(self):
        """Verify celestial omens, citizen superstition paranoia, and designating pariah scapegoats."""
        superstitions = self.engine.superstition_omens_engine
        self.assertIsNotNone(superstitions)

        # 1. Trigger blood-red lunar eclipse
        omen = superstitions.trigger_celestial_omen("BLOOD_MOON", current_tick=1000)
        self.assertEqual(omen["omen_id"], "BLOOD_MOON")
        self.assertGreater(omen["hysteria_multiplier"], 1.0)

        # 2. Evaluate citizen superstition paranoia
        sibyl = self.engine.npcs["npc_sibyl_diviner"]
        sibyl.feelings["stress"] = 0.0
        paranoia_res = superstitions.evaluate_citizen_superstition(sibyl, omen)
        self.assertGreater(paranoia_res["paranoia_surge"], 20.0)
        self.assertGreater(sibyl.get_feeling("stress"), 20.0)

        # 3. Superstitious citizens designate a scapegoat
        barnaby_beggar = self.engine.npcs["npc_barnaby_beggar"]
        barnaby_beggar.social_profile["social_class"] = "OUTCAST"

        scapegoat_res = superstitions.designate_superstitious_scapegoat(omen, [barnaby_beggar, sibyl])
        self.assertIsNotNone(scapegoat_res)
        self.assertEqual(scapegoat_res["scapegoat_npc_id"], barnaby_beggar.id)
        self.assertGreater(barnaby_beggar.get_feeling("stress"), 30.0)


if __name__ == "__main__":
    unittest.main()
