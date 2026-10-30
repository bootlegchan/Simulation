"""
Test Suite for Clandestine Cults, Social Scandals, Survival Economics,
and Deep Psychological Moral Erosion (Milestone V32).
"""
import unittest
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject
from src.behaviours.actions import ActionRegistry
from src.society.cults import CultOrder, CultRank, CultRiteEngine, InquisitionAndHysteriaEngine
from src.society.scandals_and_taboos import (
    TabooType,
    OstracismOrder,
    SocialOstracismEngine,
    ViceEscapismDen,
)
from src.economy.indenture import IndentureContract, IndentureManager, ContrabandFencingRing
from src.npc.moral_erosion import (
    MoralAlignment,
    MoralErosionTracker,
    CognitiveDissonanceEngine,
)

class TestCultsScandalsAndDarkUnderworld(unittest.TestCase):
    """Verifies cult orders, ostracism, indenture peonage, vice dens, and moral erosion."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_01_clandestine_cult_order_and_esoteric_rites(self):
        """Verify cult creation, esoteric rite conduct, and inquisition interrogation."""
        silas = self.engine.npcs["npc_silas"]
        beatrice = self.engine.npcs["npc_beatrice"]
        oswald = self.engine.npcs["npc_oswald_guard"]

        cult = CultOrder(
            cult_id="cult_veiled_moon",
            name="Order of the Veiled Moon",
            doctrine="Seek illumination beyond municipal decrees in subterranean night.",
            inner_sanctum_room_id="room_black_market_cellar",
            leader_id=silas.id
        )
        cult.induct_member(silas.id, CultRank.HIEROPHANT)
        cult.induct_member(beatrice.id, CultRank.ACOLYTE)

        altar = self.engine.objects["object_occult_altar"]
        tome = ItemInstance("inst_tome_1", "item_occult_tome", 100.0, 100.0, 1.0, owner_id=silas.id)
        silas.inventory.append(tome)

        initial_silas_erosion = silas.moral_erosion

        # Conduct esoteric rite
        rite_res = ActionRegistry.conduct_cult_rite(
            cult=cult,
            participants=[silas, beatrice],
            altar_obj=altar,
            occult_tome_item=tome,
            current_tick=500
        )
        self.assertTrue(rite_res["success"])
        self.assertTrue(rite_res["tome_amplified"])
        self.assertEqual(cult.rites_conducted_count, 1)
        self.assertGreater(silas.needs["conviction"], 50.0)
        self.assertGreater(silas.moral_erosion, initial_silas_erosion)

        # Moral panic & inquisition
        inquisition_engine = InquisitionAndHysteriaEngine()
        panic = inquisition_engine.trigger_moral_panic(
            suspected_cult_id=cult.cult_id,
            instigator_npc_id="npc_barnaby_priest",
            evidence_description="Occult sigils discovered near the cellar vault.",
            current_tick=520
        )
        self.assertEqual(panic["hysteria_level"], 75.0)

        # Interrogate suspect with pressure bonus from guard authority
        interrogate_res = inquisition_engine.interrogate_suspect(
            inquisition_id=panic["inquisition_id"],
            inquisitor=oswald,
            suspect=beatrice,
            cult=cult,
            current_tick=530,
            pressure_bonus=15.0
        )
        self.assertTrue(interrogate_res["confessed"])
        self.assertLess(cult.secrecy_rating, 90.0)
        self.assertGreater(beatrice.get_feeling("guilt"), 30.0)

    def test_02_social_scandals_taboos_and_ostracism(self):
        """Verify taboo violation, social ostracism, merchant markups, and shunning."""
        tobias = self.engine.npcs["npc_tobias"]
        aldous = self.engine.npcs["npc_aldous"]
        ostracism_engine = SocialOstracismEngine()

        # Issue ostracism on Tobias for extortion
        order = ostracism_engine.issue_ostracism(
            target_npc=tobias,
            taboo=TabooType.EXPOSED_EXTORTIONIST,
            reason="Caught operating blackmail ledger against town citizens.",
            current_tick=100
        )
        self.assertTrue(ostracism_engine.is_shunned(tobias.id))
        self.assertTrue(tobias.social_profile.get("is_shunned"))
        self.assertGreater(tobias.get_feeling("loneliness"), 40.0)

        # Merchant price gouging on pariahs (50% markup)
        normal_price = 10.0
        shunned_price = ostracism_engine.calculate_merchant_markup(tobias.id, normal_price)
        self.assertEqual(shunned_price, 15.0)

        # Citizen turns back on pariah
        shun_res = ActionRegistry.enforce_social_ostracism(ostracism_engine, aldous, tobias)
        self.assertTrue(shun_res["shunned"])
        self.assertGreater(tobias.get_feeling("loneliness"), 55.0)

        # Reconciliation / penance
        reconciled = ostracism_engine.grant_reconciliation(tobias)
        self.assertTrue(reconciled)
        self.assertFalse(ostracism_engine.is_shunned(tobias.id))
        self.assertFalse(tobias.social_profile.get("is_shunned"))

    def test_03_survival_economics_debt_indenture_and_fencing(self):
        """Verify debt indenture peonage, wage garnishment, and contraband fencing."""
        barnaby = self.engine.npcs["npc_barnaby_beggar"]
        marcus = self.engine.npcs["npc_marcus_vance"]
        indenture_mgr = IndentureManager()

        # Issue Indenture Contract for 60 Gold debt
        contract_res = ActionRegistry.issue_indenture_bond(
            indenture_mgr=indenture_mgr,
            debtor=barnaby,
            master=marcus,
            debt_amount=60.0,
            current_tick=200
        )
        self.assertTrue(contract_res["success"])
        self.assertTrue(barnaby.social_profile.get("is_indentured"))
        self.assertEqual(barnaby.get_feeling("pride"), 0.0)

        # Garnish wages from labor
        garnish_res1 = ActionRegistry.garnish_indentured_wages(
            indenture_mgr=indenture_mgr,
            contract_id=contract_res["contract_id"],
            earned_wage=40.0,
            debtor=barnaby,
            master=marcus
        )
        self.assertTrue(garnish_res1["success"])
        self.assertEqual(garnish_res1["garnished_to_master"], 30.0)
        self.assertEqual(garnish_res1["kept_by_debtor"], 10.0)
        self.assertEqual(garnish_res1["remaining_debt"], 30.0)
        self.assertFalse(garnish_res1["is_fulfilled"])

        # Second wage cycle pays off remainder
        garnish_res2 = ActionRegistry.garnish_indentured_wages(
            indenture_mgr=indenture_mgr,
            contract_id=contract_res["contract_id"],
            earned_wage=40.0,
            debtor=barnaby,
            master=marcus
        )
        self.assertTrue(garnish_res2["is_fulfilled"])
        self.assertFalse(barnaby.social_profile.get("is_indentured"))

        # Contraband Fencing
        fence_counter = self.engine.objects["object_fence_broker_counter"]
        ring = ItemInstance("inst_stolen_ring", "heirloom_engraved_signet_ring", 100.0, 100.0, 1.0, owner_id=barnaby.id)
        barnaby.inventory.append(ring)
        fence_res = ActionRegistry.fence_contraband_or_stolen(
            thief=barnaby,
            broker_counter=fence_counter,
            stolen_item=ring,
            item_base_value=250.0
        )
        self.assertTrue(fence_res["success"])
        self.assertEqual(fence_res["laundered_payout"], 150.0)  # 40% cut taken by fence broker

    def test_04_underground_vice_den_and_lotus_escapism(self):
        """Verify lotus resin escapism and underground gambling."""
        tobias = self.engine.npcs["npc_tobias"]
        resin = ItemInstance("inst_resin_1", "contraband_lotus_resin", 100.0, 100.0, 1.0, owner_id=tobias.id)
        tobias.inventory.append(resin)

        tobias.set_feeling("stress", 70.0)
        tobias.set_feeling("grief", 60.0)

        # Consume lotus resin
        resin_res = ActionRegistry.indulge_vice_den(
            npc=tobias,
            den_action_type="CONSUME_LOTUS_RESIN",
            item_or_object=resin
        )
        self.assertTrue(resin_res["success"])
        self.assertLess(tobias.get_feeling("stress"), 30.0)
        self.assertLess(tobias.get_feeling("grief"), 30.0)

        # Underground gambling with loaded dice
        gambling_pit = self.engine.objects["object_vice_gambling_pit"]
        dice = ItemInstance("inst_dice_1", "item_loaded_dice", 100.0, 100.0, 1.0, owner_id=tobias.id)
        tobias.inventory.append(dice)
        tobias.wealth = 50.0

        gamble_res = ActionRegistry.indulge_vice_den(
            npc=tobias,
            den_action_type="GAMBLE_DICE",
            item_or_object=gambling_pit,
            wager_gold=20.0,
            random_roll=0.40  # Beats 0.35 threshold with loaded dice
        )
        self.assertTrue(gamble_res["success"])
        self.assertTrue(gamble_res["won"])
        self.assertEqual(gamble_res["net_profit"], 20.0)

    def test_05_moral_erosion_and_crisis_of_conscience(self):
        """Verify moral alignment degradation and psychological crises of conscience."""
        aldous = self.engine.npcs["npc_aldous"]
        priest = self.engine.npcs["npc_barnaby_priest"]
        tracker = MoralErosionTracker(npc_id=aldous.id, erosion_score=15.0)

        self.assertEqual(tracker.alignment, MoralAlignment.VIRTUOUS)

        # Advance erosion
        tracker.advance_erosion(45.0)
        self.assertEqual(tracker.alignment, MoralAlignment.DEPRAVED)
        self.assertGreater(tracker.paranoia_score, 20.0)

        # Clash of conscience: honorable citizen overwhelmed by guilt
        aldous.set_feeling("guilt", 85.0)
        aldous.set_feeling("stress", 75.0)

        dissonance_res = ActionRegistry.evaluate_and_trigger_crisis_of_conscience(aldous, tracker)
        self.assertTrue(dissonance_res["triggered"])
        self.assertEqual(dissonance_res["break_type"], "CRISIS_OF_CONSCIENCE")
        self.assertEqual(aldous.current_state, "CRISIS_OF_CONSCIENCE")

        # Penitent confession to Priest Barnaby
        confess_res = CognitiveDissonanceEngine.execute_penitent_confession(aldous, priest, tracker)
        self.assertTrue(confess_res["success"])
        self.assertEqual(aldous.current_state, "ABSOLVED_PENITENT")
        self.assertLess(aldous.get_feeling("guilt"), 40.0)

if __name__ == "__main__":
    unittest.main()
