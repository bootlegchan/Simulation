"""
Test Suite for Expanded Content, Emotional Feelings, Physical Intimacy,
Domestic Living, Illicit Intrigue, and Open-Minded Relationship Dynamics.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject
from src.behaviours.actions import ActionRegistry
from src.society.romance import InterpersonalBond, RelationshipStage, AgreementType, AffectionStyle
from src.society.relationships import SocialNetwork
from src.ai.utility import UtilityEvaluator

class TestExpandedContentFeelingsAndIntimacy(unittest.TestCase):
    """Verifies expanded content, physical intimacy actions, domestic dynamics, and feeling transformations."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.social_net = SocialNetwork()

    def test_01_expanded_items_and_recipes_loading(self):
        """Verify all new items and recipes are loaded into engine definitions."""
        items = self.engine.item_definitions
        self.assertIn("gift_courtship_bouquet", items)
        self.assertIn("item_soothing_balm", items)
        self.assertIn("heirloom_engraved_signet_ring", items)
        self.assertIn("item_personal_diary", items)
        self.assertIn("tool_lockpick_set", items)
        self.assertIn("letter_blackmail_hook", items)
        self.assertIn("contraband_moonshine", items)
        self.assertIn("food_spiced_cider", items)

        recipes = self.engine.recipes
        self.assertIn("recipe_distill_moonshine", recipes)
        self.assertIn("recipe_brew_spiced_cider", recipes)
        self.assertIn("recipe_craft_soothing_balm", recipes)
        self.assertIn("recipe_craft_lockpicks", recipes)
        self.assertIn("recipe_craft_bouquet", recipes)

    def test_02_expanded_objects_loading_and_capabilities(self):
        """Verify new objects are registered and expose correct capabilities."""
        objects = self.engine.objects
        self.assertIn("object_canopy_bed", objects)
        self.assertIn("object_family_hearth", objects)
        self.assertIn("object_writing_desk", objects)
        self.assertIn("object_cedar_chest", objects)
        self.assertIn("object_tavern_stage", objects)
        self.assertIn("object_hidden_cache", objects)
        self.assertIn("object_clandestine_dead_drop", objects)
        self.assertIn("object_moonshine_still", objects)

        bed = objects["object_canopy_bed"]
        self.assertTrue(bed.has_capability("private_intimacy"))
        self.assertTrue(bed.has_capability("sleep"))

        hearth = objects["object_family_hearth"]
        self.assertTrue(hearth.has_capability("family_gathering"))

    def test_03_physical_intimacy_and_courtship_actions(self):
        """Verify courtship gifts, private intimacy execution, and comfort actions update feelings and bonds."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        bond = InterpersonalBond(aldous.id, beatrice.id, romantic_affection=55.0, stage=RelationshipStage.COURTING)

        # 1. Court with gift
        bouquet = ItemInstance("inst_bq_1", "gift_courtship_bouquet", 100.0, 100.0, 1.0, owner_id=aldous.id)
        aldous.inventory.append(bouquet)

        court_res = ActionRegistry.court_with_gift(aldous, beatrice, bouquet, bond, self.social_net)
        self.assertTrue(court_res["success"])
        self.assertGreater(beatrice.get_feeling("tenderness"), 20.0)
        self.assertGreater(aldous.get_feeling("pride"), 30.0)
        self.assertNotIn(bouquet, aldous.inventory)
        self.assertIn(bouquet, beatrice.inventory)

        # 2. Private intimacy in canopy bed
        canopy_bed = self.engine.objects["object_canopy_bed"]
        intimacy_res = ActionRegistry.execute_private_intimacy(
            actor=aldous,
            partner=beatrice,
            bond=bond,
            canopy_bed=canopy_bed,
            room_privacy=85.0
        )
        self.assertTrue(intimacy_res["success"])
        self.assertGreater(aldous.get_feeling("passion"), 40.0)
        self.assertGreater(beatrice.get_feeling("passion"), 40.0)
        self.assertEqual(aldous.get_feeling("loneliness"), 0.0)
        self.assertEqual(beatrice.get_feeling("loneliness"), 0.0)
        self.assertTrue(intimacy_res["stage_advanced"])
        self.assertEqual(bond.stage, RelationshipStage.LOVERS)

        # 3. Comfort partner with soothing balm
        balm = ItemInstance("inst_balm_1", "item_soothing_balm", 100.0, 100.0, 1.0, owner_id=aldous.id)
        aldous.inventory.append(balm)
        beatrice.set_feeling("grief", 60.0)
        beatrice.set_feeling("stress", 50.0)

        comfort_res = ActionRegistry.comfort_partner(aldous, beatrice, bond, balm)
        self.assertTrue(comfort_res["success"])
        self.assertTrue(comfort_res["balm_applied"])
        self.assertLess(beatrice.get_feeling("grief"), 30.0)
        self.assertLess(beatrice.get_feeling("stress"), 25.0)

    def test_04_domestic_living_hearth_and_heirlooms(self):
        """Verify family hearth gatherings, diary writing, and heirloom inspection."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        hearth = self.engine.objects["object_family_hearth"]

        # 1. Family hearth gathering
        hearth_res = ActionRegistry.gather_at_family_hearth([aldous, beatrice], hearth)
        self.assertTrue(hearth_res["success"])
        self.assertGreater(aldous.get_feeling("contentment"), 50.0)
        self.assertLessEqual(aldous.get_feeling("loneliness"), 10.0)

        # 2. Inspecting family heirloom
        ring = ItemInstance("inst_ring_1", "heirloom_engraved_signet_ring", 100.0, 100.0, 1.0, owner_id=aldous.id)
        aldous.inventory.append(ring)
        heirloom_res = ActionRegistry.inspect_family_heirloom(aldous, ring)
        self.assertTrue(heirloom_res["success"])
        self.assertGreater(aldous.get_feeling("pride"), 50.0)

        # 3. Diary writing at desk
        desk = self.engine.objects["object_writing_desk"]
        diary = ItemInstance("inst_diary_1", "item_personal_diary", 100.0, 100.0, 1.0, owner_id=aldous.id)
        aldous.inventory.append(diary)
        diary_res = ActionRegistry.write_in_diary(aldous, desk, diary, "Tonight the stars over Oakwood brought peace.", current_tick=100)
        self.assertTrue(diary_res["success"])
        self.assertEqual(diary_res["entries_total"], 1)

    def test_05_illicit_clandestine_and_blackmail_actions(self):
        """Verify clandestine rendezvous, eavesdropping, and blackmail extortion."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        tobias = self.engine.npcs["npc_tobias"]

        # Clandestine meeting with Tobias eavesdropping
        rendezvous_res = ActionRegistry.clandestine_rendezvous(
            lover_a=aldous,
            lover_b=beatrice,
            secluded_location_id="room_black_market_cellar",
            eavesdropper_ids=[tobias]
        )
        self.assertTrue(rendezvous_res["success"])
        self.assertTrue(rendezvous_res["is_intercepted"])
        self.assertTrue(rendezvous_res["blackmail_hook_generated"])

        # Tobias now has a blackmail letter
        hook_items = [i for i in tobias.inventory if i.item_def_id == "letter_blackmail_hook"]
        self.assertEqual(len(hook_items), 1)
        hook = hook_items[0]

        # Blackmail extortion of Aldous
        initial_aldous_wealth = aldous.wealth
        extort_res = ActionRegistry.blackmail_extort(
            extortionist=tobias,
            victim=aldous,
            blackmail_letter=hook,
            demanded_gold=25.0
        )
        self.assertTrue(extort_res["success"])
        self.assertLess(aldous.wealth, initial_aldous_wealth)
        self.assertGreater(aldous.get_feeling("stress"), 30.0)
        self.assertGreater(aldous.get_feeling("resentment"), 40.0)

    def test_06_emotional_feeling_dynamics_and_utility_drives(self):
        """Verify NPC feelings profile, dominant mood evaluation, and drive impact on utilities."""
        aldous = self.engine.npcs["npc_aldous"]
        self.assertEqual(aldous.get_dominant_mood(), "CONTENT")

        # Induce grief
        aldous.set_feeling("grief", 70.0)
        self.assertEqual(aldous.get_dominant_mood(), "GRIEVING")

        # Induce jealousy
        aldous.set_feeling("grief", 0.0)
        aldous.set_feeling("jealousy", 80.0)
        self.assertEqual(aldous.get_dominant_mood(), "JEALOUS")

        # Evaluate utility drives when passion and tenderness are surging
        aldous.set_feeling("jealousy", 0.0)
        aldous.set_feeling("passion", 75.0)
        aldous.set_feeling("tenderness", 60.0)
        self.assertEqual(aldous.get_dominant_mood(), "PASSIONATE")

        utilities = UtilityEvaluator.evaluate_drives(
            needs=aldous.needs,
            personality=aldous.personality,
            feelings=aldous.feelings
        )
        self.assertIn("seek_intimacy", utilities)
        self.assertGreater(utilities["seek_intimacy"], 70.0)
        self.assertIn("couple_stroll", utilities)
        self.assertIn("flirt_and_tease", utilities)

        # Decay feelings
        aldous.decay_feelings()
        self.assertLess(aldous.get_feeling("passion"), 75.0)

    def test_07_couple_stroll_and_cooperative_tasks(self):
        """Verify couples strolling together synchronized and cooperative shared tasks."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        bond = InterpersonalBond(aldous.id, beatrice.id, stage=RelationshipStage.LOVERS)

        # 1. Couple stroll
        stroll_res = ActionRegistry.couple_stroll(
            lead_npc=aldous,
            partner_npc=beatrice,
            bond=bond,
            destination_location_id="room_village_square",
            current_tick=50
        )
        self.assertTrue(stroll_res["success"])
        self.assertEqual(aldous.location_id, "room_village_square")
        self.assertEqual(beatrice.location_id, "room_village_square")
        self.assertEqual(aldous.current_state, "COUPLE_STROLLING")
        self.assertEqual(beatrice.current_state, "COUPLE_STROLLING")
        self.assertGreater(aldous.get_feeling("contentment"), 40.0)
        self.assertGreater(beatrice.get_feeling("contentment"), 40.0)

        # 2. Cooperative work task (cooking at family hearth)
        hearth = self.engine.objects["object_family_hearth"]
        task_res = ActionRegistry.cooperative_work_task(
            worker_a=aldous,
            worker_b=beatrice,
            task_type="COOPERATIVE_COOKING",
            station_object=hearth,
            bond=bond
        )
        self.assertTrue(task_res["success"])
        self.assertEqual(task_res["teamwork_efficiency_bonus"], 0.25)
        self.assertGreater(aldous.get_feeling("tenderness"), 30.0)
        self.assertGreater(beatrice.get_feeling("tenderness"), 30.0)
        self.assertGreater(bond.trust, 50.0)

    def test_08_flirtation_and_boundary_negotiation(self):
        """Verify playful flirting and communicative relationship boundary negotiations."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        bond = InterpersonalBond(aldous.id, beatrice.id, stage=RelationshipStage.ACQUAINTANCE)

        # 1. Flirt and tease
        flirt_res = ActionRegistry.flirt_and_tease(aldous, beatrice, bond=bond, is_playful=True)
        self.assertTrue(flirt_res["success"])
        self.assertGreater(aldous.get_feeling("passion"), 20.0)
        self.assertGreater(beatrice.get_feeling("passion"), 20.0)
        self.assertEqual(bond.stage, RelationshipStage.CRUSH)

        # 2. Proactive Boundary Discussion
        disc_res = ActionRegistry.discuss_relationship_boundaries(
            actor=aldous,
            partner=beatrice,
            bond=bond,
            proposed_agreement=AgreementType.OPEN_POLYAMOROUS,
            boundaries=["prior_disclosure", "mutual_respect", "safe_communal_spaces"]
        )
        self.assertTrue(disc_res["success"])
        self.assertEqual(bond.agreement_type, AgreementType.OPEN_POLYAMOROUS)
        self.assertIn("prior_disclosure", bond.declared_boundaries)
        self.assertGreater(bond.trust, 60.0)
        self.assertLessEqual(aldous.get_feeling("stress"), 10.0)

    def test_09_open_polyamorous_agreements_and_compersion(self):
        """Verify that open/polyamorous agreements prevent wrongful infidelity flags and generate compersion."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        silas = self.engine.npcs["npc_silas"]

        # Set up Open Polyamorous Agreement between Aldous and Beatrice
        bond = InterpersonalBond(
            aldous.id,
            beatrice.id,
            stage=RelationshipStage.LOVERS,
            agreement_type=AgreementType.OPEN_POLYAMOROUS,
            jealousy_threshold=30.0
        )

        # Beatrice has outside romantic encounter with Silas, with prior disclosure
        eval_res = bond.evaluate_outside_encounter(rival_id=silas.id, is_disclosed=True)
        self.assertFalse(eval_res["is_breach"])
        self.assertTrue(eval_res["compersion"])
        self.assertGreater(eval_res["compersion_boost"], 0.0)
        self.assertEqual(bond.stage, RelationshipStage.LOVERS)  # Relationship stage is preserved!
        self.assertGreaterEqual(bond.trust, 50.0)               # Trust is NOT collapsed!

        # Compare to Monogamous Exclusive baseline
        exclusive_bond = InterpersonalBond(
            aldous.id,
            beatrice.id,
            stage=RelationshipStage.LOVERS,
            agreement_type=AgreementType.MONOGAMOUS_EXCLUSIVE
        )
        exclusive_eval = exclusive_bond.evaluate_outside_encounter(rival_id=silas.id, is_disclosed=True)
        self.assertTrue(exclusive_eval["is_breach"])
        self.assertEqual(exclusive_bond.stage, RelationshipStage.EXES)  # Collapses to EXES
        self.assertEqual(exclusive_bond.trust, -100.0)

    def test_10_conflict_mediation_and_restorative_resolution(self):
        """Verify restorative conflict mediation resolves boundary breaches and jealousy."""
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]
        mediator_priest = self.engine.npcs["npc_barnaby_priest"]

        bond = InterpersonalBond(aldous.id, beatrice.id, stage=RelationshipStage.LOVERS, trust=20.0)
        aldous.set_feeling("jealousy", 60.0)
        aldous.set_feeling("resentment", 50.0)
        beatrice.set_feeling("jealousy", 40.0)
        beatrice.set_feeling("resentment", 45.0)

        # Priest Barnaby mediates conflict
        med_res = ActionRegistry.mediate_relationship_conflict(
            mediator=mediator_priest,
            partner_a=aldous,
            partner_b=beatrice,
            bond=bond
        )
        self.assertTrue(med_res["success"])
        self.assertGreater(bond.trust, 40.0)
        self.assertLess(aldous.get_feeling("jealousy"), 35.0)
        self.assertLess(aldous.get_feeling("resentment"), 20.0)
        self.assertLess(beatrice.get_feeling("jealousy"), 15.0)
        self.assertLess(beatrice.get_feeling("resentment"), 15.0)

if __name__ == "__main__":
    unittest.main()
