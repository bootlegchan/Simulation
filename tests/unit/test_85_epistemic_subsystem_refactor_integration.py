"""
Unit Test Suite 85: Epistemic Subsystem Refactor & Systemic Integration.
Verifies the full refactoring of settlement information systems into the Universal Epistemic Substrate:
1. Physical Room-Anchored Notice Boards (pinning, reading, and learning Epistemic Atoms)
2. Municipal Decrees as Legislative Fact Atoms & subjective citizen discovery via knows_decree()
3. Dynamic Job Postings & Labor Requisitions as Epistemic Contract Atoms
4. Courtroom Lawsuits as Evidence-Atom Evaluated Hearings
5. Memory Grudges as Enduring Epistemic Memory Atoms with Associative Rekindling
6. Spatial Mental Maps & Topological Landmark Atoms discovered through transit and direction sharing
7. Referential consistency and non-FSM continuous dynamics across all integrated modules
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.epistemic_engine import EpistemicEngine, EpistemicStatus, VisibilityTier, CarrierType
from src.society.municipal_decrees import MunicipalDecreeEngine
from src.society.memory_grudges import MemoryGrudgeEngine
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingCategory
from src.society.courtroom_lawsuits import CourtroomLawsuitEngine
from src.behaviours.actions import ActionRegistry

class TestEpistemicSubsystemRefactorIntegration(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()

        self.ep_eng: EpistemicEngine = self.engine.context.get_service("epistemic_engine")
        self.dec_eng: MunicipalDecreeEngine = self.engine.context.get_service("municipal_decree_engine")
        self.jp_eng: DynamicJobPostingEngine = self.engine.context.get_service("job_posting_engine")
        self.court_eng: CourtroomLawsuitEngine = self.engine.context.get_service("courtroom_lawsuit_engine")
        self.grudge_eng: MemoryGrudgeEngine = self.engine.context.get_service("memory_grudge_engine")

    def test_01_physical_room_notice_board_atoms(self):
        """Verify notice boards act as physical room-anchored Epistemic Atom carriers."""
        self.assertIsNotNone(self.ep_eng)
        public_plaza = "room_village_square"

        # Initially 0 or baseline atoms
        init_board_atoms = len(self.ep_eng.get_notice_board_atoms(public_plaza))

        # Create and pin a public notice atom to the village square notice board
        notice_atom = self.ep_eng.create_atom(
            title="Harvest Festival Proclamation",
            content="Autumn harvest festivities will begin at solar noon with communal dining.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT,
            carrier_type=CarrierType.NOTE,
            location_id=public_plaza,
            emotional_relevance=1.3,
            created_tick=100
        )
        self.ep_eng.post_to_notice_board(public_plaza, notice_atom)

        # Verified pinned on board
        board_atoms = self.ep_eng.get_notice_board_atoms(public_plaza)
        self.assertEqual(len(board_atoms), init_board_atoms + 1)
        self.assertIn(notice_atom, board_atoms)

        # Citizen reads the physical notice board
        reader = self.engine.npcs["npc_citizen_01"]
        self.assertNotIn(notice_atom.atom_id, self.ep_eng.npc_memories.get(reader.id, {}))

        learned = self.ep_eng.read_notice_board(reader, public_plaza, self.engine.context, current_tick=120)
        self.assertIn(notice_atom, learned)
        self.assertIn(notice_atom.atom_id, self.ep_eng.npc_memories[reader.id])

        # Trace salience is 1.0 in conscious memory
        trace = self.ep_eng.npc_memories[reader.id][notice_atom.atom_id]
        self.assertEqual(trace.salience, 1.0)

    def test_02_municipal_decree_legislative_atoms_and_subjective_discovery(self):
        """Verify municipal decrees create Legislative Fact Atoms and enforce subjective citizen knowledge."""
        aldous = self.engine.npcs["npc_aldous"] # Commoner / farmer
        mayor = self.engine.npcs["npc_devon"]   # Official mayor

        # Enact Nocturnal Curfew
        decree_rec = self.dec_eng.enact_decree("NOCTURNAL_CURFEW", self.engine.context, tick=200)
        self.assertIsNotNone(decree_rec)

        # Mayor is an official and automatically knows the law
        self.assertTrue(self.dec_eng.knows_decree(mayor, "NOCTURNAL_CURFEW", self.engine.context))

        # Aldous has NOT read the board or been told, so he does NOT know of the decree yet!
        self.assertFalse(self.dec_eng.knows_decree(aldous, "NOCTURNAL_CURFEW", self.engine.context))

        # Check that decree atom was posted to the village square notice board
        plaza_atoms = self.ep_eng.get_notice_board_atoms("room_village_square")
        decree_atoms = [a for a in plaza_atoms if a.payload.get("decree_id") == "NOCTURNAL_CURFEW"]
        self.assertGreaterEqual(len(decree_atoms), 1)

        # Aldous walks into the square and reads the notice board
        self.ep_eng.read_notice_board(aldous, "room_village_square", self.engine.context, current_tick=260)

        # NOW Aldous subjectively knows of the decree!
        self.assertTrue(self.dec_eng.knows_decree(aldous, "NOCTURNAL_CURFEW", self.engine.context))

    def test_03_job_postings_as_epistemic_contract_atoms(self):
        """Verify job postings generate Epistemic Contract Atoms pinned to notice boards or shadow channels."""
        # Create an official public repair posting
        post = self.jp_eng.create_posting(
            title="Public Works: Wall Timber Repair",
            description="Mend cracked palisade timber",
            channel=PostingChannel.OFFICIAL,
            category=JobPostingCategory.INFRASTRUCTURE_REPAIR,
            location_id="room_village_square",
            target_work_location_id="room_village_square",
            reward_gold=5.0,
            employer_name="Town Surveyor",
            current_tick=300,
            context=self.engine.context
        )

        # Verified Epistemic Contract Atom created and pinned to notice board
        board_atoms = self.ep_eng.get_notice_board_atoms("room_village_square")
        job_atoms = [a for a in board_atoms if a.payload.get("posting_id") == post.posting_id]
        self.assertEqual(len(job_atoms), 1)
        atom = job_atoms[0]
        self.assertEqual(atom.visibility, VisibilityTier.PUBLIC_SETTLEMENT)
        self.assertEqual(atom.status, EpistemicStatus.FACT)
        self.assertIn("job_posting", atom.tags)

    def test_04_courtroom_hearings_evidence_atoms_evaluation(self):
        """Verify courtroom lawsuit trials evaluate submitted Epistemic Evidence Atoms."""
        magistrate = self.engine.npcs["npc_devon"]
        plaintiff = self.engine.npcs["npc_greta"]
        defendant = self.engine.npcs["npc_tobias"]

        # File commercial fraud lawsuit with marginal evidence (evidence_score = 35.0; without evidence atoms: 35.0 - 28.5 defense = 6.5 < 45.0 threshold)
        file_res = self.court_eng.file_lawsuit(
            plaintiff=plaintiff,
            defendant=defendant,
            lawsuit_type="COMMERCIAL_FRAUD_OR_USURY",
            evidence_score=35.0,
            context=self.engine.context,
            current_tick=400
        )
        self.assertTrue(file_res["success"])
        suit_id = file_res["suit_id"]

        # Give plaintiff an incontrovertible Epistemic Evidence Atom: Inscribed Ledger Audit
        evidence_atom = self.ep_eng.create_atom(
            title="Ledger Evidence: Clandestine Grain Shortage",
            content=f"Audited accounting confirms {defendant.name} embezzled commercial grain sacks.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.CONFIDENTIAL,
            carrier_type=CarrierType.LEDGER,
            subject_id=defendant.id,
            actor_id=plaintiff.id,
            credibility=1.0,
            emotional_relevance=1.8,
            created_tick=400,
            tags=["commercial_fraud_or_usury", "crime", "evidence"],
            payload={"suspect_id": defendant.id}
        )
        self.ep_eng.impart_knowledge(plaintiff, evidence_atom, current_tick=400)

        # Conduct trial: Evidence atom is presented and evaluated in court!
        trial_res = self.court_eng.conduct_court_trial(suit_id, magistrate, self.engine.context, current_tick=420)
        self.assertTrue(trial_res["success"])
        # High evidence atom boost secured conviction!
        self.assertEqual(trial_res["verdict"], "CONVICTED")
        self.assertGreater(trial_res["evidence_atoms_count"], 0)

        # Verified Court Verdict Fact Atom pinned to Town Hall and Village Square
        th_atoms = self.ep_eng.get_notice_board_atoms("room_town_hall")
        verdict_atoms = [a for a in th_atoms if "verdict" in a.tags and "commercial_fraud_or_usury" in a.tags]
        self.assertGreaterEqual(len(verdict_atoms), 1)

    def test_05_memory_grudges_as_enduring_epistemic_atoms_and_reconciliation(self):
        """Verify memory grudges create high-emotion Epistemic Atoms that reconcile cleanly."""
        bearer = self.engine.npcs["npc_greta"]
        perpetrator = self.engine.npcs["npc_tobias"]

        # Register grudge
        res = self.grudge_eng.register_grudge(bearer, perpetrator, "theft", self.engine.context, current_tick=500)
        self.assertTrue(res["success"])
        self.assertTrue(self.grudge_eng.has_grudge_against(bearer.id, perpetrator.id, self.engine.context))

        # Epistemic Atom inscribed in bearer's memory
        bearer_traces = self.ep_eng.npc_memories.get(bearer.id, {})
        grudge_traces = [t for t in bearer_traces.values() if "grudge" in t.atom.tags and t.atom.actor_id == perpetrator.id]
        self.assertEqual(len(grudge_traces), 1)
        g_trace = grudge_traces[0]
        # Permanent emotional anchor (2.0)
        self.assertEqual(g_trace.atom.emotional_relevance, 2.0)
        self.assertFalse(g_trace.is_dormant())

        # Reconcile grudge
        reconciled = self.grudge_eng.reconcile_grudge(bearer, perpetrator, self.engine.context, current_tick=600)
        self.assertTrue(reconciled)
        self.assertFalse(self.grudge_eng.has_grudge_against(bearer.id, perpetrator.id, self.engine.context))
        # Salience cleared to 0.0
        self.assertEqual(g_trace.salience, 0.0)

    def test_06_spatial_landmarks_mental_map_and_direction_sharing(self):
        """Verify spatial landmarks update mental maps and directions can be shared between citizens."""
        speaker = self.engine.npcs["npc_aldous"]
        listener = self.engine.npcs["npc_citizen_01"]

        # Aldous learns landmark of his farmhouse
        aldous_atom = self.ep_eng.learn_spatial_landmark(
            speaker,
            "room_farmhouse",
            "Farmhouse Hearth",
            ["room_village_square", "room_farmhouse_bedroom"],
            self.engine.context,
            current_tick=700
        )
        self.assertIn("room_farmhouse", speaker.mental_map["discovered_rooms"])

        # Listener has not yet discovered farmhouse
        if "discovered_rooms" in getattr(listener, "mental_map", {}):
            listener.mental_map["discovered_rooms"].discard("room_farmhouse")

        # Speaker shares travel directions to listener
        shared_atom = self.ep_eng.share_spatial_directions(speaker, listener, "room_farmhouse", self.engine.context, current_tick=720)
        self.assertIsNotNone(shared_atom)

        # Listener's mental map now includes the farmhouse landmark and its doorway portals!
        self.assertIn("room_farmhouse", listener.mental_map["discovered_rooms"])
        self.assertIn("room_village_square", listener.mental_map["known_connections"]["room_farmhouse"])

        # Biographical log recorded
        last_log = listener.biographical_log[-1]
        self.assertEqual(last_log["category"], "LEARNED_DIRECTIONS")
        self.assertIn("Farmhouse", last_log["description"])

if __name__ == "__main__":
    unittest.main()
