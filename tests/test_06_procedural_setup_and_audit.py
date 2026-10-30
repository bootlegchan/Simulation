"""
Consolidated Test Suite 06: Bounded Procedural Generation, Town Setup, Accuracy Engines, and Audits.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.core.randomness import SeededRandom
from src.simulation.engine import SimulationEngine
from src.world.grammars import MacroZoningGrammar
from src.npc.archetypes import NPCArchetypeGrammar
from src.configuration.constraint_solver import ConstraintSolver
from src.npc.kinship import KinshipGraph, KinshipRelation
from src.world.history import SettlementHistoryGenerator
from src.economy.prebalance import PrebalanceEngine
from src.configuration.world_setup import TownSetupEngine
from src.diagnostics.intentionality_auditor import IntentionalityAuditor
from src.society.relationships import SocialNetwork


class TestProceduralSetupAndAudit(unittest.TestCase):
    """Verifies Bounded Procedural Generation, Town Setup, Backstory Seeding, and Simulation Audits."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.random_gen = SeededRandom(seed=42)
        self.social_net = SocialNetwork()

    def test_bounded_procedural_generation_and_constraint_solver(self):
        grammar = MacroZoningGrammar()
        macro_res = grammar.validate_settlement_zoning(
            self.engine.settlements["settlement_oakwood"],
            len(self.engine.npcs),
            self.engine.spatial_graph
        )
        self.assertTrue(macro_res.get("valid", True))

        # Test Micro Trait Grammar Sanitization
        aldous = self.engine.npcs["npc_aldous"]
        sanitized = NPCArchetypeGrammar.sanitize_and_mutate_npc(aldous)
        self.assertIsNotNone(sanitized)

        # Constraint Solver
        solver = ConstraintSolver()
        solver_res = solver.solve_and_sanitize_world(
            self.engine.settlements["settlement_oakwood"],
            self.engine.npcs,
            self.engine.spatial_graph
        )
        self.assertTrue(solver_res.get("solved_successfully", True))

    def test_town_setup_kinship_backstory_and_pareto_wealth(self):
        kin = KinshipGraph()
        aldous = self.engine.npcs["npc_aldous"]
        beatrice = self.engine.npcs["npc_beatrice"]

        kin.register_relation(aldous.id, beatrice.id, KinshipRelation.SPOUSE)
        self.assertEqual(kin.get_relation(aldous.id, beatrice.id), KinshipRelation.SPOUSE)

        # Backstory Seeding
        history = SettlementHistoryGenerator.generate_town_history(
            settlement_name="Oakwood",
            npcs=self.engine.npcs,
            social_network=self.social_net,
            random_gen=self.random_gen,
            history_years=10
        )
        self.assertGreaterEqual(len(history), 1)

        # Prebalance Engine
        pre_res = PrebalanceEngine.prebalance_market_and_pantries(
            npcs=self.engine.npcs,
            item_definitions=self.engine.item_definitions,
            pantries_and_chests=self.engine.objects
        )
        self.assertIn("food_bread", pre_res["baseline_prices"])

        # Town Setup Engine
        setup_eng = TownSetupEngine(self.random_gen)
        setup_res = setup_eng.setup_town_and_population(
            settlement_name="Oakwood",
            npcs=self.engine.npcs,
            social_network=self.social_net,
            pantries=self.engine.objects,
            item_defs=self.engine.item_definitions
        )
        self.assertTrue(setup_res["occupational_check"]["is_balanced"])

    def test_intentionality_audit(self):
        auditor = IntentionalityAuditor()
        audit_res = auditor.run_all_intentionality_audits()
        self.assertGreater(len(audit_res), 0)
        self.assertTrue(all(r.passed for r in audit_res))


if __name__ == "__main__":
    unittest.main()
