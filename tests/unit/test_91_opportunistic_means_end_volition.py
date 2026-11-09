"""Unit Test Suite 91: Opportunistic Means-End Volition & Dynamic Moral Elasticity Engine."""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.behaviours.actions import ActionRegistry
from src.ai.means_end_volition import (
    MeansEndVolitionEngine, VolitionTier, ProblemSolvingDomain, ProblemSolvingPath, AspirationalCareerDeficit
)
from src.ai.drive_strategies import HungerDriveStrategy, WorkProductionDriveStrategy


class TestOpportunisticMeansEndVolition(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.volition_eng = self.engine.context.get_service("means_end_volition_engine")

    def test_01_multi_tier_sustenance_pathway_evaluation(self):
        """Verify that hungry NPCs evaluate conventional, compensatory, and transgressive pathways."""
        citizen = self.engine.npcs["npc_citizen_09"]
        citizen.wealth = 20.0
        citizen.needs["hunger"] = 40.0
        
        # When solvent: conventional market purchase is top viable path
        paths_solvent = self.volition_eng.evaluate_sustenance_pathways(citizen, self.engine.context, current_tick=100)
        self.assertTrue(any(p.tier == VolitionTier.CONVENTIONAL for p in paths_solvent))

        # When broke with zero food: evaluates compensatory borrowing and foraging
        citizen.wealth = 0.0
        citizen.inventory.clear()
        citizen.needs["hunger"] = 70.0
        # Co-located with Citizen 10 who has coin
        citizen.location_id = "room_village_square"
        paths_broke = self.volition_eng.evaluate_sustenance_pathways(citizen, self.engine.context, current_tick=200)
        
        tiers = [p.tier for p in paths_broke]
        self.assertIn(VolitionTier.COMPENSATORY, tiers)
        
        # Borrowing and foraging are offered
        path_ids = [p.path_id for p in paths_broke]
        self.assertTrue("COMPENSATORY_FORAGE_SCRAPS" in path_ids or "COMPENSATORY_BORROW_FOOD" in path_ids)

    def test_02_continuous_moral_elasticity_friction_function(self):
        """Verify moral resistance discounts quadratically as physiological hunger urgency surges."""
        aldous = self.engine.npcs["npc_aldous"]
        aldous.social_profile.setdefault("moral_values", {})["honor"] = 0.8
        aldous.personality["conscientiousness"] = 0.85

        # Well-fed baseline: urgency = 1.0 -> High moral resistance
        res_calm = self.volition_eng.calculate_effective_moral_resistance(aldous, urgency=1.0, action_base_moral_cost=35.0)
        self.assertGreater(res_calm, 40.0)

        # Starving emergency: urgency = 3.5 -> Severe quadratic discount
        res_starving = self.volition_eng.calculate_effective_moral_resistance(aldous, urgency=3.5, action_base_moral_cost=35.0)
        self.assertLess(res_starving, 10.0)
        self.assertLess(res_starving, res_calm * 0.25)

    def test_03_petty_shoplifting_execution_and_guilt_aftermath(self):
        """Verify executing transgressive shoplifting relieves hunger but inflicts guilt, stress, and leaves clue atoms."""
        rogue = self.engine.npcs["npc_tobias"]
        rogue.wealth = 0.0
        rogue.inventory.clear()
        rogue.needs["hunger"] = 85.0
        hh_eng = self.engine.context.get_service("household_economy_engine")
        if hh_eng:
            hh = hh_eng.get_household_for_npc(rogue.id)
            if hh:
                hh.pantry_food_rations = 0.0
        rogue.feelings["guilt"] = 0.0
        rogue.feelings["stress"] = 5.0
        rogue.location_id = "room_bakery"
        # Shopkeeper is asleep at home, so no friendly food sharing is possible
        greta = self.engine.npcs["npc_greta"]
        greta.location_id = "room_farmhouse_bedroom"

        res = self.volition_eng.execute_sustenance_problem_solving(rogue, self.engine.context, current_tick=300)
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "PETTY_SHOPLIFTING")

        # Hunger was relieved by stolen bread!
        self.assertLessEqual(rogue.needs["hunger"], 45.0)
        # Incurred psychological guilt and moral friction
        self.assertGreater(rogue.feelings["guilt"], 15.0)
        self.assertGreater(rogue.feelings["stress"], 10.0)

        # Forensic clue atom recorded in bakery
        ep_eng = self.engine.context.get_service("epistemic_engine")
        clues = ep_eng.room_clues.get("room_bakery", [])
        self.assertGreaterEqual(len(clues), 1)

    def test_04_multi_tier_courtship_seclusion_and_indoor_trespassing(self):
        """Verify lovers without owned bedrooms evaluate rentals, secluded spots, and indoor trespassing."""
        actor = self.engine.npcs["npc_citizen_09"] # Unhoused in square
        partner = self.engine.npcs["npc_citizen_10"]
        actor.home_location_id = "room_village_square"
        partner.home_location_id = "room_village_square"
        actor.feelings["passion"] = 80.0
        partner.feelings["passion"] = 80.0
        actor.unmet_intimacy_tension = 70.0
        partner.unmet_intimacy_tension = 70.0

        paths = self.volition_eng.evaluate_courtship_seclusion_pathways(actor, partner, self.engine.context, current_tick=400)
        path_ids = [p.path_id for p in paths]

        # Compensatory and transgressive paths are evaluated
        self.assertTrue(any(p.tier in (VolitionTier.COMPENSATORY, VolitionTier.TRANSGRESSIVE) for p in paths))
        self.assertIn("COMPENSATORY_SECLUDED_SPOT", path_ids)

        # Invitation executes successfully without hardcoded failure
        res_invite = ActionRegistry.invite_to_private_quarters(actor, partner, self.engine.context)
        self.assertTrue(res_invite["success"])
        self.assertIn(res_invite["rendezvous_type"], ("RENTED_ROOM", "SECLUDED_SPOT", "TRESPASSING_INDOORS"))

    def test_05_aspirational_career_skill_bridging(self):
        """Verify skill-deficient NPCs register career aspirations and bridge deficits through study and practice."""
        apprentice = self.engine.npcs["npc_citizen_01"]
        apprentice.skills["smithing"] = 15.0
        apprentice.mental_attributes["ambition"] = 65.0

        # Register aspiration for blacksmithing requiring 30.0 skill
        asp = self.volition_eng.register_career_aspiration(
            apprentice,
            target_occupation="Blacksmith",
            required_skill="smithing",
            required_level=30.0,
            current_level=15.0,
            current_tick=500
        )
        self.assertEqual(asp.deficit, 15.0)
        self.assertIn(apprentice.id, self.volition_eng.aspirations)

        # Advance via vocational study
        res_study = self.volition_eng.advance_vocational_skill_bridging(apprentice, method="STUDY", context=self.engine.context, current_tick=560)
        self.assertTrue(res_study["success"])
        self.assertGreater(apprentice.skills["smithing"], 15.0)
        self.assertLess(res_study["deficit_remaining"], 15.0)

        # Advance via master observation
        res_obs = self.volition_eng.advance_vocational_skill_bridging(apprentice, method="OBSERVE", context=self.engine.context, current_tick=620)
        self.assertTrue(res_obs["success"])
        self.assertGreater(apprentice.skills["smithing"], res_study["new_level"])

    def test_06_guilt_remedy_and_spiritual_confession_drive(self):
        """Verify accumulated guilt generates spiritual remorse thoughts and directs agent toward confession."""
        citizen = self.engine.npcs["npc_citizen_02"]
        citizen.feelings["guilt"] = 45.0 # Heavy guilt from past crime/transgression

        remedy = self.volition_eng.evaluate_guilt_remedy(citizen, self.engine.context, current_tick=700)
        self.assertIsNotNone(remedy)
        self.assertEqual(remedy["recommended_action"], "SPIRITUAL_CONFESSION")
        self.assertEqual(remedy["destination"], "room_chapel")

        # Mindspace recognizes moral remorse
        mind_eng = self.engine.context.get_service("attentional_mindspace_engine")
        mind_eval = mind_eng.evaluate_attentional_mindspace(citizen, self.engine.context, current_tick=700)
        titles = [t["title"] for t in mind_eval["spotlight_thoughts"]]
        self.assertTrue(any("Remorse" in t or "Guilt" in t for t in titles))


if __name__ == "__main__":
    unittest.main()
