"""
Consolidated Test Suite 03: AI Decision Making, GOAP, Utility Evaluator, Senses, Memory, and Cognition.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.core.randomness import SeededRandom
from src.simulation.engine import SimulationEngine
from src.ai.utility import UtilityEvaluator
from src.ai.goap import GOAPPlanner, Goal, Action
from src.ai.fsm import FSMController, FSMState
from src.ai.blackboard import Blackboard
from src.npc.memory import MemorySystem
from src.senses.perception import PerceptionSystem
from src.senses.communication import CommunicationChannel
from src.senses.inquiry import ConversationalInquiryEngine
from src.senses.hub import SensoryHub
from src.npc.reflection import ReflectionEngine


class TestAISensesAndCognition(unittest.TestCase):
    """Verifies UtilityEvaluator, GOAP Planner, Senses, Multi-Store Memory, and Reflection Engine."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.random_gen = SeededRandom(seed=42)

    def test_utility_evaluator_s_curves_and_softmax_logit_sampling(self):
        needs = {"hunger": 75.0, "energy": 30.0, "social": 20.0, "wealth": 10.0}
        personality = {"openness": 0.5, "conscientiousness": 0.8, "extraversion": 0.6, "agreeableness": 0.7, "neuroticism": 0.3}

        utilities = UtilityEvaluator.evaluate_drives(needs, personality=personality)
        self.assertIn("satisfy_hunger", utilities)
        self.assertIn("rest", utilities)
        self.assertGreater(utilities["satisfy_hunger"], 50.0)

        probs = UtilityEvaluator.calculate_softmax_probabilities(utilities, temperature=10.0)
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=4)

        choice, prob, prob_dict = UtilityEvaluator.sample_choice_multinomial_logit(utilities, self.random_gen, temperature=10.0)
        self.assertIn(choice, utilities)
        self.assertGreater(prob, 0.0)

    def test_goap_planner_a_star_pathfinding(self):
        actions = [
            Action("get_raw_wheat", preconditions={"has_wheat": False}, effects={"has_wheat": True}, cost=1.0),
            Action("grind_flour", preconditions={"has_wheat": True, "has_flour": False}, effects={"has_flour": True}, cost=2.0),
            Action("bake_bread", preconditions={"has_flour": True, "has_bread": False}, effects={"has_bread": True}, cost=1.0),
        ]
        goal = Goal("satisfy_hunger", target_state={"has_bread": True})
        initial_state = {"has_wheat": False, "has_flour": False, "has_bread": False}

        plan = GOAPPlanner.plan(initial_state, goal, actions)
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0].name, "get_raw_wheat")
        self.assertEqual(plan[2].name, "bake_bread")

    def test_fsm_controller_and_blackboard(self):
        blackboard = Blackboard()
        blackboard.set("hunger_level", 80.0)
        self.assertEqual(blackboard.get("hunger_level"), 80.0)

        fsm = FSMController()
        self.assertEqual(fsm.state, FSMState.IDLE)

        fsm.set_plan([{"action": "eat"}])
        self.assertEqual(fsm.state, FSMState.EXECUTING_ACTION)

    def test_stratified_memory_and_associative_retrieval(self):
        mem_sys = MemorySystem(retention_half_life=50.0)

        # 1. Sensory Buffer
        mem_sys.record_sensory_input("perceived_item", "item_bread", tick=10, payload={"location": "table"})
        self.assertEqual(len(mem_sys.sensory_buffer), 1)

        # 2. Episodic Recording & Ebbinghaus Decay
        mem_sys.record("mem_1", "crime_witnessed", "npc_tobias", tick=10, payload={"crime": "theft"}, salience=8.0)
        mem_sys.record("mem_2", "conversation", "npc_silas", tick=12, payload={"topic": "wheat"}, salience=1.0)

        mem_sys.apply_ebbinghaus_decay(current_tick=100)
        mems = mem_sys.query(event_type="crime_witnessed")
        self.assertEqual(len(mems), 1)
        self.assertGreater(mems[0].retention_strength, 5.0)

        # 3. Associative Retrieval Scoring
        results = mem_sys.associative_retrieval_query("tobias theft crime", current_tick=100, top_k=2)
        self.assertGreater(len(results), 0)
        top_mem, score = results[0]
        self.assertEqual(top_mem.subject_id, "npc_tobias")

        # 4. Sleep Memory Consolidation
        consolidated = mem_sys.consolidate_memories(current_tick=100)
        self.assertGreater(consolidated, 0)
        self.assertEqual(len(mem_sys.sensory_buffer), 0)
        self.assertIn("perceived:perceived_item:item_bread", mem_sys.semantic_beliefs)

    def test_sensory_hub_and_conversational_inquiry(self):
        hub = SensoryHub()
        aldous = self.engine.npcs["npc_aldous"]
        silas = self.engine.npcs["npc_silas"]

        # PerceptionSystem
        room = self.engine.settlements["settlement_oakwood"].buildings["bldg_vance_manor"].rooms["room_vance_shop_floor"]
        obs = hub.perception_system.observe_room(room, observer_id=aldous.id, current_tick=10)
        self.assertIsNotNone(obs)

        # Inquiry engine
        inquiry_res = ConversationalInquiryEngine.evaluate_and_execute_inquiry(
            inquirer=aldous,
            respondent=silas,
            inquirer_memory=MemorySystem(),
            respondent_memory=MemorySystem(),
            current_tick=50,
            topic_key="stolen_bread_investigation"
        )
        self.assertIsNotNone(inquiry_res)
        self.assertEqual(inquiry_res.inquirer_id, aldous.id)

    def test_reflection_engine_and_mind_state_insights(self):
        beatrice = self.engine.npcs["npc_beatrice"]
        mem_sys = MemorySystem()
        mem_sys.record("m1", "crime_witnessed", "npc_vance", tick=10, payload={"detail": "affair"}, salience=9.0)
        mem_sys.record("m2", "crime_witnessed", "npc_tobias", tick=20, payload={"detail": "theft"}, salience=8.0)

        insight = ReflectionEngine.evaluate_and_trigger_reflection("npc_beatrice", mem_sys, current_tick=100, importance_threshold=50.0)
        self.assertIsNotNone(insight)


if __name__ == "__main__":
    unittest.main()
