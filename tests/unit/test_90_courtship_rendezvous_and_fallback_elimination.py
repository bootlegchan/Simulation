"""Unit Test Suite 90: Courtship Seclusion (Rentals & Secluded Spaces) and Fallback Elimination."""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.behaviours.actions import ActionRegistry
from src.entities.occupations import OccupationRegistry
from src.economy.intelligent_food_selection import IntelligentFoodSelector
from src.configuration.settings import SettingsRegistry
from src.ai.drive_strategies import CommunalDiningDriveStrategy


class TestCourtshipRendezvousAndFallbackElimination(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

    def test_01_courtship_housed_couple_retires_to_home_bedchamber(self):
        """Verify that a couple with a private domestic bedchamber retires to their own home."""
        aldous = self.engine.npcs["npc_aldous"]
        greta = self.engine.npcs["npc_greta"]
        aldous.location_id = "room_village_square"
        greta.location_id = "room_village_square"

        res = ActionRegistry.invite_to_private_quarters(aldous, greta, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["rendezvous_type"], "HOME_BEDCHAMBER")
        self.assertIn("farmhouse_bedroom", res["destination"])
        self.assertEqual(aldous.location_id, res["destination"])
        self.assertEqual(greta.location_id, res["destination"])
        self.assertEqual(res["rental_fee_paid"], 0.0)

    def test_02_courtship_unhoused_couple_rents_private_tavern_room(self):
        """Verify that an unhoused couple with funds rents a tavern loft for short-term seclusion."""
        actor = self.engine.npcs["npc_citizen_09"]
        partner = self.engine.npcs["npc_citizen_17"]

        # Both reside in village square (no home bedroom)
        actor.home_location_id = "room_village_square"
        partner.home_location_id = "room_village_square"
        actor.location_id = "room_village_square"
        partner.location_id = "room_village_square"

        actor.wealth = 15.0
        partner.wealth = 10.0

        # High rapport for consent
        rom_eng = self.engine.context.get_service("romance_engine")
        bond = rom_eng.get_or_create_bond(actor.id, partner.id, context=self.engine.context)
        bond.romantic_affection = 70.0
        bond.trust = 70.0
        bond.physical_attraction = 70.0

        silas = self.engine.npcs["npc_silas"]
        init_silas_wealth = silas.wealth

        res = ActionRegistry.invite_to_private_quarters(actor, partner, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["rendezvous_type"], "RENTED_ROOM")
        self.assertEqual(res["destination"], "room_tavern_bedroom")
        self.assertEqual(res["rental_fee_paid"], 0.50)
        self.assertAlmostEqual(actor.wealth, 14.50, places=2)
        # Closed-loop: Innkeeper Silas received the rental fee
        self.assertAlmostEqual(silas.wealth, init_silas_wealth + 0.50, places=2)

    def test_03_courtship_penniless_couple_seeks_secluded_unowned_space(self):
        """Verify that an impoverished couple with zero funds retreats to a secluded unowned space with clandestine thrill."""
        actor = self.engine.npcs["npc_citizen_09"]
        partner = self.engine.npcs["npc_citizen_17"]

        actor.home_location_id = "room_village_square"
        partner.home_location_id = "room_village_square"
        actor.location_id = "room_village_square"
        partner.location_id = "room_village_square"

        actor.wealth = 0.0
        partner.wealth = 0.0

        rom_eng = self.engine.context.get_service("romance_engine")
        bond = rom_eng.get_or_create_bond(actor.id, partner.id, context=self.engine.context)
        bond.romantic_affection = 70.0
        bond.trust = 70.0
        bond.physical_attraction = 70.0

        init_passion = actor.feelings.get("passion", 15.0)

        res = ActionRegistry.invite_to_private_quarters(actor, partner, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["rendezvous_type"], "SECLUDED_SPOT")
        # Retreats to secluded candidate like farmhouse loft or cottage
        self.assertTrue(any(k in res["destination"] for k in ("loft", "hayloft", "cellar", "meadow", "orchard", "woods", "brook", "garden", "cottage", "bedroom")))
        self.assertEqual(res["rental_fee_paid"], 0.0)
        # Clandestine passion thrill applied
        self.assertGreater(actor.feelings["passion"], init_passion)

    def test_04_communal_dining_price_dynamically_loaded_from_settings(self):
        """Verify that communal dining reads meal price dynamically from culinary_economy.json without hardcoding."""
        citizen = self.engine.npcs["npc_citizen_01"]
        citizen.wealth = 10.0
        citizen.location_id = "room_tavern"

        settings = SettingsRegistry.get_instance()
        cul_cfg = settings.get("culinary_economy")
        orig_price = cul_cfg.get("communal_dining", {}).get("tavern_meal_price_gold", 1.20)

        try:
            # Override meal price in settings to 2.50g
            cul_cfg["communal_dining"]["tavern_meal_price_gold"] = 2.50
            settings.set_override("culinary_economy", cul_cfg)

            strat = CommunalDiningDriveStrategy()
            act = strat.execute(citizen, self.engine.context, 100, "2026-01-01T08:00:00", 8, {})
            self.assertEqual(act, "COMMUNAL_DINING")
            # Deducted 2.50g, not hardcoded 1.0g
            self.assertAlmostEqual(citizen.wealth, 7.50, places=2)
        finally:
            cul_cfg["communal_dining"]["tavern_meal_price_gold"] = orig_price
            settings.set_override("culinary_economy", cul_cfg)

    def test_05_intelligent_food_selection_uses_dynamic_market_price(self):
        """Verify that food selection queries supply chain market price rather than hardcoded 3.0."""
        diner = self.engine.npcs["npc_citizen_01"]
        sc_eng = self.engine.context.get_service("supply_chain_engine")

        # In baseline, bread market price is calculated dynamically from stock level
        expected_p = sc_eng.calculate_market_price("food_bread")
        candidates = IntelligentFoodSelector.assemble_candidates(diner, self.engine.context)
        bakery_cands = [c for c in candidates if "baker" in c.source_name.lower() or "bread" in c.item_def_id]

        self.assertGreater(len(bakery_cands), 0)
        self.assertAlmostEqual(bakery_cands[0].price_gold, expected_p, places=1)

    def test_06_vocational_default_skills_loaded_from_declarative_occupations(self):
        """Verify that OccupationRegistry default skills derive from occupations.json global_skill_baselines."""
        occ_reg = OccupationRegistry.get_instance()
        skills = occ_reg.get_default_skills("Farmer")

        self.assertEqual(skills["farming"], 65.0)
        self.assertEqual(skills["crafting"], 30.0)
        self.assertEqual(skills["baking"], 20.0)
        self.assertEqual(skills["brawling"], 20.0)
        self.assertEqual(skills["subterfuge"], 15.0)

    def test_07_notice_board_and_crime_room_fallback_resolves_dynamically(self):
        """Verify that notice board and crime reporting fallbacks resolve to real rooms, never 'room_plaza'."""
        reader = self.engine.npcs["npc_citizen_01"]
        reader.location_id = None # Force fallback

        res_board = ActionRegistry.read_notice_board(reader, self.engine.context)
        self.assertTrue(res_board["success"])

        guard = self.engine.npcs["npc_citizen_16"]
        res_crime = ActionRegistry.report_crime_to_watch(reader, guard, "Theft", "Stolen goods", None, self.engine.context)
        self.assertTrue(res_crime["success"])


if __name__ == "__main__":
    unittest.main()
