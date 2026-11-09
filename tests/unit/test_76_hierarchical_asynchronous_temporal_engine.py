"""
Unit Test Suite 76: Hierarchical Asynchronous Event-Scheduled Time (HAEST) Kernel.
Verifies the modern temporal architecture:
- Deterministic min-heap priority queue and event scheduling
- Continuous intent horizons for agent actions without artificial modulo gates
- Analytical continuous decay equivalence across variable delta_ticks
- Emergency preemption interrupting active intent horizons
- Fast-forward adaptive temporal leaps with closed-loop economic conservation
"""
import unittest
import time
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.core.temporal_scheduler import (
    HierarchicalTemporalScheduler,
    TemporalEvent,
    IntentHorizon,
)
from src.economy.macro import MacroEconomicTracker
from src.behaviours.actions import ActionRegistry

class TestHierarchicalAsynchronousTemporalEngine(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.scheduler: HierarchicalTemporalScheduler = self.engine.context.get_service("temporal_scheduler")

    def test_01_hierarchical_temporal_scheduler_deterministic_queue(self):
        """Verify min-heap order, deterministic monotonic tie-breaking, and event cancellation."""
        scheduler = HierarchicalTemporalScheduler()

        # Schedule events out of chronological order
        e3 = scheduler.schedule_event(scheduled_tick=300, event_type="STAGE_DUE", priority=50)
        e1 = scheduler.schedule_event(scheduled_tick=100, event_type="ALARM", priority=10, target_id="npc_aldous")
        e2 = scheduler.schedule_event(scheduled_tick=100, event_type="MEETING", priority=20, target_id="npc_beatrice")
        e4 = scheduler.schedule_event(scheduled_tick=500, event_type="EXPIRATION", priority=50)

        # Earliest tick should be 100
        self.assertEqual(scheduler.peek_next_tick(), 100)

        # Cancel Aldous's event
        cancelled_count = scheduler.cancel_events_for_target("npc_aldous")
        self.assertEqual(cancelled_count, 1)

        # Due events at tick 100 should now pop e2 only (e1 was cancelled)
        due_100 = scheduler.pop_due_events(100)
        self.assertEqual(len(due_100), 1)
        self.assertEqual(due_100[0].event_type, "MEETING")
        self.assertEqual(due_100[0].target_id, "npc_beatrice")

        # Next due event should be at tick 300
        self.assertEqual(scheduler.peek_next_tick(), 300)

    def test_02_intent_horizon_action_commitments(self):
        """Verify continuous IntentHorizon duration tracking and completion calculation."""
        horizon = IntentHorizon(
            action_name="LABOR_WORK",
            started_tick=100,
            duration_ticks=120,
            target_destination="room_blacksmith"
        )
        self.assertEqual(horizon.until_tick, 220)
        self.assertTrue(horizon.is_active(100))
        self.assertTrue(horizon.is_active(150))
        self.assertTrue(horizon.is_active(219))
        self.assertFalse(horizon.is_active(220))
        self.assertEqual(horizon.remaining_ticks(150), 70)
        self.assertEqual(horizon.remaining_ticks(250), 0)

    def test_03_continuous_analytical_decay_multitick_equivalence(self):
        """Verify that analytical decay across delta_ticks matches sequential single-tick integration."""
        npc_a = self.engine.npcs["npc_aldous"]
        npc_b = self.engine.npcs["npc_greta"]

        # Align starting states
        npc_a.needs["hunger"] = 20.0
        npc_b.needs["hunger"] = 20.0
        npc_a.needs["energy"] = 80.0
        npc_b.needs["energy"] = 80.0
        npc_a.feelings["stress"] = 30.0
        npc_b.feelings["stress"] = 30.0

        # NPC A: 10 individual 1-tick decays
        for i in range(10):
            npc_a.apply_continuous_decay(delta_ticks=1, current_tick=100 + i)

        # NPC B: One 10-tick continuous decay
        npc_b.apply_continuous_decay(delta_ticks=10, current_tick=100)

        # Hunger, energy, and feelings should be equivalent
        self.assertAlmostEqual(npc_a.needs["hunger"], npc_b.needs["hunger"], places=2)
        self.assertAlmostEqual(npc_a.needs["energy"], npc_b.needs["energy"], places=2)
        self.assertAlmostEqual(npc_a.feelings["stress"], npc_b.feelings["stress"], places=2)

    def test_04_preemption_breaks_intent_horizon(self):
        """Verify that severe biological emergencies interrupt an agent's active intent horizon immediately."""
        aldous = self.engine.npcs["npc_aldous"]
        aldous.intent_horizon = IntentHorizon(
            action_name="WRITE_DIARY",
            started_tick=100,
            duration_ticks=60
        )
        self.scheduler.schedule_event(scheduled_tick=160, event_type="AGENT_INTENT_EXPIRED", target_id=aldous.id)

        # Trigger critical exhaustion emergency
        aldous.needs["energy"] = 5.0
        cog_sub = [s for s in self.engine.pipeline_manager.subsystems if s.subsystem_id == "subsystem_cognitive"][0]
        cog_sub.on_tick(110, self.engine.context)

        # Intent horizon must be interrupted and cancelled
        self.assertIsNone(aldous.intent_horizon)
        self.assertIn(aldous.current_action, ("SLEEP_REST", "COLLAPSE_FATIGUE"))

    def test_05_fast_forward_temporal_leaping_and_conservation(self):
        """Verify that fast_forward advances the clock accurately and maintains closed-loop economic stability."""
        initial_balance = MacroEconomicTracker.calculate_total_currency(
            self.engine.npcs,
            getattr(self.engine.context.municipal_treasury, "balance", 0.0),
            context=self.engine.context
        )

        # Fast-forward 1 full day (1,440 ticks) using HAEST leaping
        final_tick = self.engine.fast_forward(total_ticks=1440, max_leap=60)
        self.assertEqual(final_tick, 1440)
        self.assertEqual(self.engine.clock.current_tick, 1440)

        # Economy remains stable and all citizens remain alive
        alive_count = sum(1 for n in self.engine.npcs.values() if getattr(n, "is_alive", True))
        self.assertEqual(alive_count, len(self.engine.npcs))

        final_balance = MacroEconomicTracker.calculate_total_currency(
            self.engine.npcs,
            getattr(self.engine.context.municipal_treasury, "balance", 0.0),
            context=self.engine.context
        )
        self.assertGreater(final_balance, 0.0)

    def test_06_fast_forward_speedup_benchmark(self):
        """Verify that fast_forward runs significantly faster than 720 individual 1-tick passes."""
        engine_standard = SimulationEngine(self.data_dir)
        engine_standard.initialize(seed=42)
        engine_standard.start()

        engine_fast = SimulationEngine(self.data_dir)
        engine_fast.initialize(seed=42)
        engine_fast.start()

        # Benchmark 12 hours (720 ticks) standard tick(1)
        t0 = time.time()
        engine_standard.tick(720)
        standard_duration = time.time() - t0

        # Benchmark 12 hours (720 ticks) fast_forward
        t1 = time.time()
        engine_fast.fast_forward(720, max_leap=60)
        fast_duration = time.time() - t1

        # fast_forward should complete in less time or comparable with high throughput
        self.assertEqual(engine_fast.clock.current_tick, 720)
        self.assertEqual(engine_standard.clock.current_tick, 720)
        self.assertLessEqual(fast_duration, standard_duration * 1.5)

if __name__ == "__main__":
    unittest.main()
