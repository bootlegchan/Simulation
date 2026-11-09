import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.romance import RomanceEngine, RelationshipStage, InterpersonalBond
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType
from src.behaviours.actions import ActionRegistry

class TestBilateralSocialAndRomanceDynamics(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.rom_eng: RomanceEngine = self.engine.context.get_service("romance_engine")
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")

    def test_01_bilateral_consent_exhaustion_refusal(self):
        """Verify that exhausted or stressed partners refuse intimacy proposals to protect stamina."""
        actor = self.engine.npcs["npc_aldous"]
        partner = self.engine.npcs["npc_beatrice"]

        # Place both in a secluded room
        actor.location_id = "room_bedroom"
        partner.location_id = "room_bedroom"

        # Partner is exhausted (energy = 12.0 < min_energy 20.0)
        partner.needs["energy"] = 12.0
        partner.feelings["stress"] = 10.0

        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=100, context=self.engine.context)
        self.assertFalse(res["success"])
        self.assertEqual(res["details"]["reason"], "EXHAUSTION")
        # Actor suffers mild rejection grief
        self.assertGreater(actor.get_feeling("grief"), 0.0)

    def test_02_bilateral_consent_co_location_enforcement(self):
        """Verify that agents cannot perform intimacy while in different rooms across town."""
        actor = self.engine.npcs["npc_aldous"]
        partner = self.engine.npcs["npc_beatrice"]

        actor.location_id = "room_farmhouse"
        partner.location_id = "room_market" # Across town!

        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=100, context=self.engine.context)
        self.assertFalse(res["success"])
        self.assertIn("not co-located", res["reason"])

    def test_03_consensual_private_intimacy_in_bedchamber(self):
        """Verify that consensual intimacy in a private bedchamber succeeds without public scandal."""
        actor = self.engine.npcs["npc_aldous"]
        partner = self.engine.npcs["npc_beatrice"]

        actor.location_id = "room_cottage_bedroom"
        partner.location_id = "room_cottage_bedroom"
        actor.needs["energy"] = 80.0
        partner.needs["energy"] = 80.0
        actor.feelings["stress"] = 10.0
        partner.feelings["stress"] = 10.0

        bond = self.rom_eng.get_or_create_bond(actor.id, partner.id)
        bond.romantic_affection = 70.0
        bond.physical_attraction = 70.0
        bond.trust = 70.0

        initial_waves = len(self.info_eng.active_waves)

        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=100, context=self.engine.context)
        self.assertTrue(res["success"])
        self.assertTrue(res["details"]["is_private_room"])
        self.assertEqual(res["details"]["witnesses_count"], 0)

        # No public scandal emitted in a private bedroom with zero witnesses
        self.assertEqual(len(self.info_eng.active_waves), initial_waves)

    def test_04_public_clandestine_tryst_emits_scandal_wave(self):
        """Verify that intimacy attempted in a public room with witnesses emits an ambient acoustic scandal wave."""
        actor = self.engine.npcs["npc_aldous"]
        partner = self.engine.npcs["npc_beatrice"]
        witness = self.engine.npcs["npc_citizen_01"]

        # All present in the open tavern common room
        pub_room = "room_tavern"
        actor.location_id = pub_room
        partner.location_id = pub_room
        witness.location_id = pub_room

        actor.needs["energy"] = 80.0
        partner.needs["energy"] = 80.0
        # Ensure unmarried for public tryst test
        actor.social_profile["spouse_id"] = None
        partner.social_profile["spouse_id"] = None
        bond = self.rom_eng.get_or_create_bond(actor.id, partner.id)
        bond.romantic_affection = 80.0
        bond.physical_attraction = 80.0
        bond.trust = 80.0

        initial_scandals = self.rom_eng.total_scandals_emitted

        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=200, context=self.engine.context)
        self.assertTrue(res["success"])
        self.assertTrue(res["details"]["is_clandestine_public"])
        self.assertGreaterEqual(res["details"]["witnesses_count"], 1)

        # Verified scandal wave emitted
        self.assertEqual(self.rom_eng.total_scandals_emitted, initial_scandals + 1)
        scandal_waves = [w for w in self.info_eng.active_waves if self.info_eng.active_items.get(w.item_id) and self.info_eng.active_items[w.item_id].topic == "SCANDALOUS_PUBLIC_TRYST"]
        self.assertGreaterEqual(len(scandal_waves), 1)

    def test_05_marital_infidelity_detection_and_spousal_grudge(self):
        """Verify that intimacy with a third party triggers spouse resentment and high-credibility betrayal news."""
        spouse_aldous = self.engine.npcs["npc_aldous"]
        spouse_greta = self.engine.npcs["npc_greta"]
        lover_beatrice = self.engine.npcs["npc_beatrice"]

        # Formally marry Aldous and Greta
        spouse_aldous.social_profile["spouse_id"] = spouse_greta.id
        spouse_greta.social_profile["spouse_id"] = spouse_aldous.id
        spouse_greta.feelings["resentment"] = 0.0

        # Place Aldous and lover in tavern with Greta witnessing
        spouse_aldous.location_id = "room_tavern"
        lover_beatrice.location_id = "room_tavern"
        spouse_greta.location_id = "room_tavern"

        spouse_aldous.needs["energy"] = 85.0
        lover_beatrice.needs["energy"] = 85.0
        bond_tryst = self.rom_eng.get_or_create_bond(spouse_aldous.id, lover_beatrice.id)
        bond_tryst.romantic_affection = 85.0
        bond_tryst.physical_attraction = 85.0
        bond_tryst.trust = 75.0

        res = ActionRegistry.execute_private_intimacy(spouse_aldous, lover_beatrice, current_tick=300, context=self.engine.context)
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["scandal_outcome"])
        self.assertTrue(res["scandal_outcome"]["infidelity_detected"])

        # Greta suffers acute betrayal and resentment influx
        self.assertGreaterEqual(spouse_greta.get_feeling("resentment"), 40.0)
        self.assertGreaterEqual(spouse_greta.get_feeling("jealousy"), 40.0)

    def test_06_declarative_betrothal_speech_act(self):
        """Verify formal betrothal pledges register on civic notice boards and update marital intent."""
        suitor = self.engine.npcs["npc_aldous"]
        target = self.engine.npcs["npc_beatrice"]

        res = ActionRegistry.declare_betrothal(suitor, target, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["stage"], "BETROTHED")

        # Social profiles updated
        self.assertEqual(suitor.social_profile["partner_id"], target.id)
        self.assertEqual(target.social_profile["partner_id"], suitor.id)

        # Formal notice published on civic board
        civic_notices = [
            item for item in self.info_eng.active_items.values()
            if item.topic == "BETROTHAL_ANNOUNCEMENT"
        ]
        self.assertGreaterEqual(len(civic_notices), 1)
        self.assertIn("Public Banns", civic_notices[0].headline)

    def test_07_relationship_weighted_socializing_dynamics(self):
        """Verify socializing in a room with adversaries increases stress while friends provide deep fulfillment."""
        aldous = self.engine.npcs["npc_aldous"]
        aldous.location_id = "room_tavern"
        aldous.needs["social"] = 40.0
        aldous.feelings["stress"] = 20.0

        # Scenario A: Socializing around an adversary with a grudge
        enemy = self.engine.npcs["npc_tobias"]
        enemy.location_id = "room_tavern"
        grudge_eng = self.engine.context.get_service("memory_grudge_engine")
        grudge_eng.register_grudge(bearer=aldous, perpetrator=enemy, category="THEFT", current_tick=100)

        strat = self.engine.context.get_service("drive_strategy_registry").strategies["socialize"]
        strat.execute(aldous, self.engine.context, tick=100, time_iso="", hour=18, locations={})

        # Tension with adversary increased stress!
        self.assertGreater(aldous.feelings["stress"], 20.0)

        # Scenario B: Socializing with loved ones / friends
        friend = self.engine.npcs["npc_greta"]
        friend.location_id = "room_bakery"
        aldous.location_id = "room_bakery"
        enemy.location_id = "room_cellar" # Enemy leaves
        aldous.feelings["stress"] = 40.0

        op_eng = self.engine.context.get_service("directional_opinion_engine")
        op_eng.add_modifier(from_npc=aldous, to_npc=friend, mod_id="friendship", desc="Cherished bond", delta=50.0, tick=100)

        strat.execute(aldous, self.engine.context, tick=200, time_iso="", hour=18, locations={})
        # Stress greatly reduced in welcoming circle
        self.assertLess(aldous.feelings["stress"], 40.0)

    def test_08_elastic_exhibitionist_intimacy_in_public_plaza(self):
        """Verify that exhibitionist agents enthusiastically consent to intimacy in public areas and gain thrill pride."""
        actor = self.engine.npcs["npc_tobias"]
        partner = self.engine.npcs["npc_citizen_02"]

        # Place both in the open public village square
        plaza = "room_village_square"
        actor.location_id = plaza
        partner.location_id = plaza
        actor.needs["energy"] = 80.0
        partner.needs["energy"] = 80.0

        # Tobias is an uninhibited rogue with exhibitionist proclivity
        actor.vices["exhibitionism"] = 65.0
        actor.tags.add("TAG_EXHIBITIONIST")
        partner.tags.add("TAG_HEDONIST")

        bond = self.rom_eng.get_or_create_bond(actor.id, partner.id)
        bond.romantic_affection = 55.0
        bond.physical_attraction = 60.0
        bond.trust = 50.0

        # Execute intimacy in public square
        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=400, context=self.engine.context)
        self.assertTrue(res["success"], f"Failed: {res.get('reason')}")
        self.assertTrue(res["details"]["is_clandestine_public"])
        self.assertTrue(res["details"]["is_exhibitionist_act"])

        # Check exhibitionist thrill bonuses awarded
        self.assertGreaterEqual(actor.get_feeling("pride"), 20.0)
        self.assertGreaterEqual(partner.get_feeling("pride"), 20.0)
        self.assertEqual(actor.biographical_log[-1]["category"], "EXHIBITIONIST_TRYST")

    def test_09_voyeuristic_witness_titillation_and_scandal_suppression(self):
        """Verify that voyeuristic witnesses experience titillation instead of moral indignation, suppressing scandal."""
        actor = self.engine.npcs["npc_aldous"]
        partner = self.engine.npcs["npc_beatrice"]
        voyeur_witness = self.engine.npcs["npc_citizen_03"]

        pub_room = "room_tavern"
        # Ensure only the intended test witness is in the room
        for n in self.engine.npcs.values():
            if n.location_id == pub_room and n.id not in (actor.id, partner.id):
                n.location_id = "room_tavern_bedroom"

        actor.location_id = pub_room
        partner.location_id = pub_room
        voyeur_witness.location_id = pub_room

        actor.needs["energy"] = 80.0
        partner.needs["energy"] = 80.0
        bond = self.rom_eng.get_or_create_bond(actor.id, partner.id)
        bond.romantic_affection = 80.0
        bond.physical_attraction = 80.0
        bond.trust = 80.0

        # Configure witness as an active voyeur
        voyeur_witness.vices["voyeurism"] = 60.0
        voyeur_witness.tags.add("TAG_VOYEUR")
        voyeur_witness.feelings["titillation"] = 0.0

        initial_scandals = self.rom_eng.total_scandals_emitted

        res = ActionRegistry.execute_private_intimacy(actor, partner, current_tick=500, context=self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["details"]["witnesses_count"], 1)

        # Voyeur was titillated and amused, not indignantly outraged!
        self.assertGreaterEqual(voyeur_witness.get_feeling("titillation"), 20.0)
        self.assertGreaterEqual(voyeur_witness.get_feeling("contentment"), 50.0)
        self.assertEqual(voyeur_witness.biographical_log[-1]["category"], "VOYEUR_SPECTACLE")

        # Scandal was suppressed into a clandestine voyeur secret rather than public moral outrage
        voyeur_secret_waves = [
            w for w in self.info_eng.active_waves
            if self.info_eng.active_items.get(w.item_id) and self.info_eng.active_items[w.item_id].topic == "VOYEUR_CLANDESTINE_SECRET"
        ]
        self.assertGreaterEqual(len(voyeur_secret_waves), 1)

    def test_10_modest_refusal_when_sober_and_calm(self):
        """Verify that a modest, sober agent with low romance refuses public exposure, but consents elastically when intoxicated or passionate."""
        modest_actor = self.engine.npcs["npc_aldous"]
        modest_partner = self.engine.npcs["npc_citizen_04"]

        pub_plaza = "room_village_square"
        modest_actor.location_id = pub_plaza
        modest_partner.location_id = pub_plaza

        modest_partner.needs["energy"] = 80.0
        modest_partner.feelings["stress"] = 10.0
        modest_partner.feelings["passion"] = 10.0 # Low passion
        modest_partner.vices["alcohol_dependence"] = 0.0 # Sober
        modest_partner.vices["exhibitionism"] = 0.0 # Modest
        modest_partner.personality["conscientiousness"] = 0.8
        modest_partner.social_profile.setdefault("moral_values", {})["honor"] = 0.8

        bond = self.rom_eng.get_or_create_bond(modest_actor.id, modest_partner.id)
        bond.romantic_affection = 45.0
        bond.physical_attraction = 45.0
        bond.trust = 50.0

        # Attempt A: Sober, modest, low romance in public square -> Refuses public exposure
        res_sober = ActionRegistry.execute_private_intimacy(modest_actor, modest_partner, current_tick=600, context=self.engine.context)
        self.assertFalse(res_sober["success"])
        self.assertEqual(res_sober["details"]["reason"], "PUBLIC_INHIBITION")

        # Attempt B: Both partners become intoxicated and swept by passion -> Consents elastically!
        modest_actor.feelings["passion"] = 75.0
        modest_partner.feelings["passion"] = 80.0 # Overwhelming passion!
        modest_partner.vices["alcohol_dependence"] = 50.0
        bond.physical_attraction = 70.0

        res_passionate = ActionRegistry.execute_private_intimacy(modest_actor, modest_partner, current_tick=620, context=self.engine.context)
        self.assertTrue(res_passionate["success"], f"Expected elastic consent, got refusal: {res_passionate.get('reason')}")

if __name__ == "__main__":
    unittest.main()
