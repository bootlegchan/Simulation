"""
Test Suite 17: LLM Qualitative Verisimilitude & Biographical Diary Benchmark.
Tests personal life journal extraction, psychological coherence, diurnal realism,
socio-economic rationality, and the Village Verisimilitude Index (VVI).
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.diagnostics.verisimilitude_benchmark import (
    BiographicalDiaryCompiler,
    VerisimilitudeBenchmarkEngine,
    NPCBiographicalDiary,
    VerisimilitudeScorecard
)


class TestLLMVerisimilitudeAndDiaryBenchmark(unittest.TestCase):
    """Verifies that NPC lifetime logs produce realistic, human-resembling personal life diaries."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.benchmark_engine = VerisimilitudeBenchmarkEngine(self.data_dir)

    def test_01_biographical_diary_extraction(self):
        """Verify that BiographicalDiaryCompiler extracts clean chronological entries with narrative text and metrics."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(240)  # 4 hours

        aldous = engine.npcs["npc_aldous"]
        self.assertGreater(len(aldous.biographical_log), 0)

        diary = BiographicalDiaryCompiler.compile_npc_diary(aldous)
        self.assertEqual(diary.npc_id, "npc_aldous")
        self.assertEqual(diary.name, "Aldous Miller")
        self.assertGreater(len(diary.entries), 0)

        entry = diary.entries[0]
        self.assertIsNotNone(entry.time_iso)
        self.assertIsNotNone(entry.dominant_mood)
        self.assertIsNotNone(entry.narrative_entry)
        self.assertIn("hunger", entry.needs_snapshot)

    def test_02_psychological_coherence_evaluation(self):
        """Verify that emotional mood reflects physiological and psychological conditions realistically."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(1440)  # 1 full day

        beatrice = engine.npcs["npc_beatrice"]
        diary = BiographicalDiaryCompiler.compile_npc_diary(beatrice)
        scorecard = self.benchmark_engine.evaluate_npc_diary(diary)

        self.assertGreaterEqual(scorecard.psychological_coherence, 70.0)
        self.assertGreaterEqual(scorecard.composite_verisimilitude, 65.0)

    def test_03_socio_economic_and_labor_realism(self):
        """Verify that working NPCs engage in economic labor while lower-class NPCs experience resource constraints."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=42)
        engine.start()
        engine.tick(1440)

        tobias = engine.npcs["npc_tobias"]
        diary = BiographicalDiaryCompiler.compile_npc_diary(tobias)
        scorecard = self.benchmark_engine.evaluate_npc_diary(diary)

        self.assertGreaterEqual(scorecard.economic_material_adaptation, 65.0)
        self.assertGreaterEqual(scorecard.crisis_resilience, 60.0)

    def test_04_village_verisimilitude_index_benchmark(self):
        """
        Executes multi-day benchmark across key archetypal characters (Farmer, Merchant, Bard, Mayor, Priest, Smuggler)
        and asserts that the composite Village Verisimilitude Index exceeds 80.0.
        """
        sample_ids = [
            "npc_aldous",
            "npc_beatrice",
            "npc_devon",
            "npc_silas",
            "npc_tobias",
            "npc_barnaby_priest"
        ]

        benchmark_res = self.benchmark_engine.run_multi_day_benchmark(
            days=2,
            seed=42,
            eval_sample_ids=sample_ids
        )

        vvi = benchmark_res["village_verisimilitude_index"]
        dims = benchmark_res["dimension_averages"]

        # Assert composite and dimensional benchmarks
        self.assertGreater(vvi, 80.0)
        self.assertGreaterEqual(dims["psychological_coherence"], 80.0)
        self.assertGreaterEqual(dims["diurnal_rhythm_realism"], 60.0)
        self.assertGreaterEqual(dims["socio_relational_grounding"], 75.0)
        self.assertGreaterEqual(dims["economic_material_adaptation"], 75.0)
        self.assertGreaterEqual(dims["crisis_resilience"], 75.0)


if __name__ == "__main__":
    unittest.main()
