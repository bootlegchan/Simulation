"""
Unit Test Suite 84: Unified Epistemic Information System.
Verifies the multi-axial epistemic architecture:
- Epistemic Atoms (Fact, Presumption, Assumption, Guess, Internal Thought, Tutorial)
- Visibility Tiers (Internal Mind, Secret, Confidential, Private Dyadic, Public Settlement)
- Inscribed Physical Carriers (Books, Ledgers, Notes, Letters, Clues)
- Continuous Associative Memory Priming & Cue-Driven Dormant Recall
- Forensic Crime Scene Investigation & Suspect Inference
- Dyadic Conversation Continuity & Relational Social Attention Budgeting
- Introspective Reminiscing over Pivotal Life Anchors
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.item import ItemInstance
from src.society.epistemic_engine import (
    EpistemicEngine,
    EpistemicAtom,
    EpistemicStatus,
    VisibilityTier,
    CarrierType,
    EpistemicMemoryTrace,
    DyadicConversationThread,
    PhysicalInscribedCarrier,
)
from src.behaviours.actions import ActionRegistry

class TestEpistemicInformationSystem(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.ep_eng: EpistemicEngine = self.engine.context.get_service("epistemic_engine")
        self.ep_eng.clear()

    def test_01_multi_axial_epistemic_atoms_and_visibilities(self):
        """Verify multi-axial epistemic atoms with distinct truth statuses and visibility tiers."""
        self.assertIsNotNone(self.ep_eng)

        # 1. Internal Thought
        thought = self.ep_eng.create_atom(
            title="Inner Suspicion",
            content="I suspect the night guard took a bribe from Tobias.",
            status=EpistemicStatus.INTERNAL_THOUGHT,
            visibility=VisibilityTier.INTERNAL_MIND,
            actor_id="npc_aldous",
            subject_id="npc_tobias",
            emotional_relevance=1.2,
            created_tick=100
        )
        self.assertEqual(thought.status, EpistemicStatus.INTERNAL_THOUGHT)
        self.assertEqual(thought.visibility, VisibilityTier.INTERNAL_MIND)
        self.assertFalse(thought.payload.get("is_public", False))

        # 2. Secret Clandestine Atom
        secret_atom = self.ep_eng.create_atom(
            title="Clandestine Drop",
            content="Smuggled ale barrels hidden under the tavern cellar trapdoor.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.SECRET,
            actor_id="npc_tobias",
            location_id="room_tavern",
            emotional_relevance=1.7,
            created_tick=100
        )
        self.assertEqual(secret_atom.status, EpistemicStatus.FACT)
        self.assertEqual(secret_atom.visibility, VisibilityTier.SECRET)

        # 3. Public Settlement Decree Atom
        decree_atom = self.ep_eng.create_atom(
            title="Town Ordinance",
            content="Mayor Devon mandates emergency infrastructure repairs.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT,
            location_id="room_village_square",
            created_tick=100
        )
        self.assertEqual(decree_atom.visibility, VisibilityTier.PUBLIC_SETTLEMENT)

    def test_02_continuous_memory_decay_and_associative_priming(self):
        """Verify memory salience decays into dormancy and associative cues prime dormant memories back into working memory."""
        aldous = self.engine.npcs["npc_aldous"]
        tobias = self.engine.npcs["npc_tobias"]

        # Create a private memory atom regarding an encounter with Tobias at the tavern
        atom = self.ep_eng.create_atom(
            title="Tavern Confrontation",
            content="Had a sharp heated argument with Tobias regarding missing grain sheaves.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PRIVATE_DYADIC,
            actor_id=aldous.id,
            subject_id=tobias.id,
            location_id="room_tavern",
            emotional_relevance=1.6,
            created_tick=100,
            tags=["argument", "grain", "tobias"],
            associative_keys=[tobias.id, "room_tavern", "tobias", "grain"]
        )

        trace = self.ep_eng.impart_knowledge(aldous, atom, current_tick=100, salience=1.0)
        self.assertEqual(trace.salience, 1.0)
        self.assertFalse(trace.is_dormant())

        # Advance time by 3 weeks (30,000 ticks) to let memory decay into dormancy
        self.ep_eng.apply_memory_decay(aldous, current_tick=30100, delta_ticks=30000)
        self.assertLess(trace.salience, 0.15)
        self.assertTrue(trace.is_dormant())

        # Aldous walks into the tavern and sees Tobias! Sensory cues: [room_tavern, npc_tobias]
        cues = ["room_tavern", tobias.id, tobias.name.lower()]
        reactivated = self.ep_eng.evaluate_associative_priming(aldous, cues, self.engine.context, current_tick=30100)

        # Memory was primed and reactivated back into working memory!
        self.assertGreaterEqual(len(reactivated), 1)
        self.assertGreaterEqual(trace.salience, 0.15)
        self.assertFalse(trace.is_dormant())

        # Biographical log recorded
        last_log = aldous.biographical_log[-1]
        self.assertEqual(last_log["category"], "MEMORY_REKINDLED")
        self.assertIn("Tavern Confrontation", last_log["description"])

    def test_03_inscribed_physical_carriers_reading_and_learning(self):
        """Verify physical items (books, ledgers, notes) hold inscribed epistemic atoms and teach skills or reveal records upon reading."""
        smith_apprentice = self.engine.npcs["npc_citizen_12"]
        init_smithing = smith_apprentice.skills.get("smithing", 20.0)

        # Create a book item and inscribe a tutorial atom
        book_item = ItemInstance(instance_id="item_metallurgy_book_01", item_def_id="book_metallurgy_manual")
        smith_apprentice.inventory.append(book_item)

        tutorial_atom = self.ep_eng.create_atom(
            title="Iron Tempering Manual",
            content="Detailed instructions on charcoal airflow and tempering red-hot iron ingots.",
            status=EpistemicStatus.TUTORIAL_EXPLANATION,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT,
            carrier_type=CarrierType.BOOK,
            emotional_relevance=1.2,
            tags=["metallurgy", "smithing", "recipe"]
        )

        self.ep_eng.inscribe_physical_carrier(
            item_instance=book_item,
            title="Treatise on Fine Iron Forging",
            carrier_type=CarrierType.BOOK,
            atoms=[tutorial_atom],
            author_id="npc_master_smith",
            created_tick=100,
            metadata={"teaches_skill": "smithing"}
        )

        # Reader reads the physical book
        res = ActionRegistry.read_inscribed_carrier(smith_apprentice, book_item, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["carrier_type"], "BOOK")
        self.assertGreaterEqual(res["atoms_learned_count"], 1)

        # Gained practical smithing competence
        self.assertGreater(smith_apprentice.skills["smithing"], init_smithing)
        self.assertEqual(smith_apprentice.skills["smithing"], round(init_smithing + 2.0, 2))

        # Learned atom is now in apprentice's memory trace
        self.assertIn(tutorial_atom.atom_id, self.ep_eng.npc_memories[smith_apprentice.id])

    def test_04_inscribed_confidential_ledger_uncovers_records(self):
        """Verify reading a confidential town tax ledger uncovers factual administrative accounts."""
        investigator = self.engine.npcs["npc_devon"] # Mayor
        ledger_item = ItemInstance(instance_id="item_ledger_01", item_def_id="town_tax_ledger")
        investigator.inventory.append(ledger_item)

        confidential_fact = self.ep_eng.create_atom(
            title="Annual Treasury Balance Sheet",
            content="Official ledger records municipal reserve of 500 gold and commercial stall receipts.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.CONFIDENTIAL,
            carrier_type=CarrierType.LEDGER,
            emotional_relevance=1.3,
            tags=["ledger", "tax", "treasury"]
        )

        self.ep_eng.inscribe_physical_carrier(
            item_instance=ledger_item,
            title="Oakwood Tax Ledger",
            carrier_type=CarrierType.LEDGER,
            atoms=[confidential_fact],
            created_tick=100
        )

        res = ActionRegistry.read_inscribed_carrier(investigator, ledger_item, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["carrier_type"], "LEDGER")
        self.assertIn(confidential_fact.atom_id, self.ep_eng.npc_memories[investigator.id])

    def test_05_forensic_crime_investigation_and_suspect_inference(self):
        """Verify committing a crime generates act, incident, and physical clue atoms; investigation forms suspect inference."""
        thief = self.engine.npcs["npc_tobias"]
        victim = self.engine.npcs["npc_greta"]
        guard = self.engine.npcs.get("npc_citizen_16") or self.engine.npcs["npc_aldous"]
        crime_loc = "room_bakery"

        # Record a crime: Tobias burglarizes Greta's bakery
        forensics = self.ep_eng.record_crime_forensic_atoms(
            perpetrator=thief,
            victim=victim,
            crime_type="BURGLARY",
            location_id=crime_loc,
            context=self.engine.context,
            current_tick=200
        )

        self.assertIn("act_atom", forensics)
        self.assertIn("clue_atom", forensics)
        self.assertEqual(forensics["act_atom"].visibility, VisibilityTier.SECRET)
        self.assertEqual(forensics["clue_atom"].carrier_type, CarrierType.PHYSICAL_CLUE)
        self.assertIn(crime_loc, self.ep_eng.room_clues)

        # Guard arrives at the bakery and investigates the scene
        guard.location_id = crime_loc
        invest_res = ActionRegistry.investigate_crime_scene(guard, crime_loc, self.engine.context)
        self.assertTrue(invest_res["success"])
        self.assertGreaterEqual(invest_res["clues_discovered_count"], 1)

        # Guard formulated a PRESUMPTION suspect inference atom pointing to Tobias!
        guard_traces = self.ep_eng.npc_memories[guard.id]
        suspect_atoms = [
            t.atom for t in guard_traces.values()
            if t.atom.status == EpistemicStatus.PRESUMPTION and t.atom.subject_id == thief.id
        ]
        self.assertGreaterEqual(len(suspect_atoms), 1)
        self.assertTrue(suspect_atoms[0].payload.get("warrant_active"))
        self.assertIn(thief.name, suspect_atoms[0].title)

    def test_06_dyadic_conversation_threads_and_relational_priority(self):
        """Verify dyadic conversation threads track shared secrets, continuity, and calculate relational attention budgets."""
        aldous = self.engine.npcs["npc_aldous"]
        spouse = self.engine.npcs.get("npc_citizen_02") or self.engine.npcs["npc_greta"]
        aldous.social_profile["spouse_id"] = spouse.id
        spouse.social_profile["spouse_id"] = aldous.id

        # 1. Spouses have maximum relational attention priority
        priority_spouse = self.ep_eng.calculate_relational_priority(aldous, spouse, self.engine.context)
        stranger = self.engine.npcs["npc_citizen_35"]
        priority_stranger = self.ep_eng.calculate_relational_priority(aldous, stranger, self.engine.context)

        self.assertGreater(priority_spouse, priority_stranger)
        self.assertGreaterEqual(priority_spouse, 50.0)

        # 2. Dyadic thread exchange
        secret_atom = self.ep_eng.create_atom(
            title="Private Family Secret",
            content="Aldous shares hidden gold cache with spouse.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.SECRET,
            actor_id=aldous.id,
            emotional_relevance=1.6
        )

        self.ep_eng.record_dyadic_exchange(aldous, spouse, secret_atom, self.engine.context, current_tick=300)

        thread = self.ep_eng.get_dyadic_thread(aldous.id, spouse.id)
        self.assertIn(secret_atom.atom_id, thread.discussed_atom_ids)
        self.assertEqual(thread.shared_secrets_count, 1)
        self.assertEqual(thread.last_conversed_tick, 300)

    def test_07_introspective_reminiscing_over_life_anchors(self):
        """Verify agent reminisces over high-emotion life event anchors, restoring contentment and tenderness."""
        aldous = self.engine.npcs["npc_aldous"]
        spouse = self.engine.npcs.get("npc_citizen_02") or self.engine.npcs["npc_greta"]

        # Impart a high-emotion permanent marriage anchor atom (emotional_relevance = 2.0 >= 1.8)
        marriage_atom = self.ep_eng.create_atom(
            title="Sacred Wedding Vows",
            content=f"Solemn marriage vows pledged with {spouse.name} at St. Jude's Chapel.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PRIVATE_DYADIC,
            actor_id=aldous.id,
            subject_id=spouse.id,
            emotional_relevance=2.0,
            tags=["marriage", "love", "vows"]
        )
        self.ep_eng.impart_knowledge(aldous, marriage_atom, current_tick=100)

        init_tenderness = aldous.get_feeling("tenderness")
        init_contentment = aldous.get_feeling("contentment")

        res = ActionRegistry.reminisce_life_event(aldous, self.engine.context)
        self.assertTrue(res["success"])
        self.assertEqual(res["outcome"]["effect"], "rekindled_tenderness")

        # Emotional feelings rekindled by past memory
        self.assertGreater(aldous.get_feeling("tenderness"), init_tenderness)
        self.assertGreater(aldous.get_feeling("contentment"), init_contentment)

        # Biographical log recorded
        last_log = aldous.biographical_log[-1]
        self.assertEqual(last_log["category"], "REMINISCE_PAST")
        self.assertIn("Sacred Wedding Vows", last_log["description"])

if __name__ == "__main__":
    unittest.main()
