"""
Test Suite 14: Subsystem Pipeline Kernel, WorldContext Facade, and Data-Driven Architecture.
Verifies stage-pipelined execution, topological priority ordering, frequency gating,
WorldContext service locator, dynamic registration, and state persistence.
"""
import unittest
from pathlib import Path
from typing import Any, Dict, List

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.core.subsystem import (
    ISimulationSubsystem,
    SubsystemPipelineManager,
    TickStage,
    TickFrequency,
)
from src.core.context import WorldContext
from src.core.events import DomainEvent


class MockExecutionTrackerSubsystem(ISimulationSubsystem):
    """Test subsystem that logs execution order and ticks."""

    def __init__(self, sub_id: str, stage: TickStage, priority: int, frequency: int = 1):
        self.subsystem_id = sub_id
        self.name = f"Mock {sub_id}"
        self.tick_stage = stage
        self.execution_priority = priority
        self.tick_frequency = frequency
        self.is_enabled = True

        self.execution_log: List[str] = []
        self.received_events: List[str] = []
        self.custom_state: int = 100

    def initialize(self, context: WorldContext) -> None:
        self.execution_log.append("initialized")

    def on_tick(self, tick: int, context: WorldContext) -> None:
        tracker = context.get_service("global_execution_tracker", [])
        tracker.append((self.subsystem_id, self.tick_stage.value, self.execution_priority, tick))
        context.register_service("global_execution_tracker", tracker)
        self.execution_log.append(f"tick_{tick}")
        self.custom_state += 1

    def handle_event(self, event: DomainEvent, context: WorldContext) -> None:
        self.received_events.append(event.event_type)

    def save_state(self) -> Dict[str, Any]:
        return {"custom_state": self.custom_state, "log_count": len(self.execution_log)}

    def load_state(self, data: Dict[str, Any]) -> None:
        self.custom_state = data.get("custom_state", 100)


class TestSubsystemPipelineKernel(unittest.TestCase):
    """Verifies that the engine operates as a decoupled microkernel with data-driven subsystems."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_01_subsystem_manifest_loading_and_registration(self):
        """Verify that all subsystems declared in subsystems_manifest.json are dynamically loaded."""
        pipeline = self.engine.pipeline_manager
        self.assertIsNotNone(pipeline)
        self.assertGreaterEqual(len(pipeline.subsystems), 8)

        # Verify key expected subsystems
        self.assertIn("biosphere_and_climate", pipeline.subsystems)
        self.assertIn("infrastructure_and_sanitation", pipeline.subsystems)
        self.assertIn("cognitive_agents", pipeline.subsystems)
        self.assertIn("economy_and_finance", pipeline.subsystems)
        self.assertIn("urban_lifecycle", pipeline.subsystems)
        self.assertIn("guild_cartels", pipeline.subsystems)

        # Check stage buckets
        pre_tick_subs = pipeline._stage_buckets[TickStage.PRE_TICK]
        self.assertGreater(len(pre_tick_subs), 0)
        cognitive_subs = pipeline._stage_buckets[TickStage.COGNITIVE_DECISION]
        self.assertGreater(len(cognitive_subs), 0)
        post_tick_subs = pipeline._stage_buckets[TickStage.POST_TICK_MAINTENANCE]
        self.assertGreater(len(post_tick_subs), 0)

    def test_02_world_context_service_container(self):
        """Verify WorldContext service registration, entity access facades, and decoupled helpers."""
        ctx = self.engine.context
        self.assertIsNotNone(ctx)

        # Entity collections
        self.assertIn("settlement_oakwood", ctx.settlements)
        self.assertIn("npc_aldous", ctx.npcs)
        self.assertIn("object_canopy_bed", ctx.objects)

        # Service locator
        self.assertTrue(ctx.has_service("urban_growth_engine"))
        self.assertTrue(ctx.has_service("credit_instrument_manager"))
        self.assertTrue(ctx.has_service("guild_cartel_manager"))

        # Decoupled entity lookups
        aldous = ctx.get_npc("npc_aldous")
        self.assertIsNotNone(aldous)
        self.assertEqual(aldous.name, "Aldous Miller")

        bed = ctx.get_object("object_canopy_bed")
        self.assertIsNotNone(bed)
        self.assertTrue(bed.has_capability("private_intimacy"))

        room = ctx.find_room_by_id("room_village_square")
        self.assertIsNotNone(room)

    def test_03_stage_topological_execution_order(self):
        """Verify that subsystems execute in strict stage order: PRE_TICK -> COGNITIVE -> EXECUTION -> POST_TICK."""
        manager = SubsystemPipelineManager()
        ctx = WorldContext()
        ctx.register_service("global_execution_tracker", [])

        # Register subsystems in deliberately mixed stage order
        post_sub = MockExecutionTrackerSubsystem("sub_post", TickStage.POST_TICK_MAINTENANCE, priority=10)
        pre_sub = MockExecutionTrackerSubsystem("sub_pre", TickStage.PRE_TICK, priority=10)
        exec_sub = MockExecutionTrackerSubsystem("sub_exec", TickStage.EXECUTION_ACTION, priority=10)
        cog_sub = MockExecutionTrackerSubsystem("sub_cog", TickStage.COGNITIVE_DECISION, priority=10)

        manager.register_subsystem(post_sub)
        manager.register_subsystem(pre_sub)
        manager.register_subsystem(exec_sub)
        manager.register_subsystem(cog_sub)

        # Dispatch tick 1
        manager.dispatch_tick(tick=1, context=ctx)
        tracker = ctx.get_service("global_execution_tracker")

        # Must execute in strict topological stage order
        stage_sequence = [entry[1] for entry in tracker]
        self.assertEqual(
            stage_sequence,
            [
                TickStage.PRE_TICK.value,
                TickStage.COGNITIVE_DECISION.value,
                TickStage.EXECUTION_ACTION.value,
                TickStage.POST_TICK_MAINTENANCE.value,
            ]
        )

    def test_04_execution_priority_within_same_stage(self):
        """Verify that within a stage, subsystems execute in ascending priority order (lower priority integer first)."""
        manager = SubsystemPipelineManager()
        ctx = WorldContext()
        ctx.register_service("global_execution_tracker", [])

        sub_p50 = MockExecutionTrackerSubsystem("sub_p50", TickStage.PRE_TICK, priority=50)
        sub_p10 = MockExecutionTrackerSubsystem("sub_p10", TickStage.PRE_TICK, priority=10)
        sub_p30 = MockExecutionTrackerSubsystem("sub_p30", TickStage.PRE_TICK, priority=30)

        manager.register_subsystem(sub_p50)
        manager.register_subsystem(sub_p10)
        manager.register_subsystem(sub_p30)

        manager.dispatch_tick(tick=1, context=ctx)
        tracker = ctx.get_service("global_execution_tracker")

        sub_sequence = [entry[0] for entry in tracker]
        self.assertEqual(sub_sequence, ["sub_p10", "sub_p30", "sub_p50"])

    def test_05_frequency_interval_gating(self):
        """Verify that subsystems with higher frequencies (e.g. 60 or 1440) only execute on matching intervals."""
        manager = SubsystemPipelineManager()
        ctx = WorldContext()
        ctx.register_service("global_execution_tracker", [])

        sub_hourly = MockExecutionTrackerSubsystem("sub_hourly", TickStage.PRE_TICK, priority=10, frequency=60)
        sub_daily = MockExecutionTrackerSubsystem("sub_daily", TickStage.POST_TICK_MAINTENANCE, priority=10, frequency=1440)
        sub_always = MockExecutionTrackerSubsystem("sub_always", TickStage.EXECUTION_ACTION, priority=10, frequency=1)

        manager.register_subsystem(sub_hourly)
        manager.register_subsystem(sub_daily)
        manager.register_subsystem(sub_always)

        # Tick 1: only sub_always should run
        ctx.register_service("global_execution_tracker", [])
        manager.dispatch_tick(tick=1, context=ctx)
        ran_subs_1 = [e[0] for e in ctx.get_service("global_execution_tracker")]
        self.assertEqual(ran_subs_1, ["sub_always"])

        # Tick 60: sub_always and sub_hourly should run
        ctx.register_service("global_execution_tracker", [])
        manager.dispatch_tick(tick=60, context=ctx)
        ran_subs_60 = [e[0] for e in ctx.get_service("global_execution_tracker")]
        self.assertIn("sub_always", ran_subs_60)
        self.assertIn("sub_hourly", ran_subs_60)
        self.assertNotIn("sub_daily", ran_subs_60)

        # Tick 1440: all three should run
        ctx.register_service("global_execution_tracker", [])
        manager.dispatch_tick(tick=1440, context=ctx)
        ran_subs_1440 = [e[0] for e in ctx.get_service("global_execution_tracker")]
        self.assertEqual(len(ran_subs_1440), 3)
        self.assertIn("sub_daily", ran_subs_1440)

    def test_06_dynamic_runtime_subsystem_registration(self):
        """Verify dynamically registering a custom subsystem into an initialized engine at runtime."""
        custom_sub = MockExecutionTrackerSubsystem(
            sub_id="sub_custom_mod",
            stage=TickStage.EXECUTION_ACTION,
            priority=5,
            frequency=1
        )
        self.engine.register_subsystem(custom_sub)

        self.assertIn("sub_custom_mod", self.engine.pipeline_manager.subsystems)
        self.assertIn("initialized", custom_sub.execution_log)

        # Advance engine tick
        self.engine.tick(count=1)
        self.assertIn("tick_1", custom_sub.execution_log)

    def test_07_event_broadcasting_across_pipeline(self):
        """Verify broadcasting DomainEvents to all registered subsystems."""
        custom_sub = MockExecutionTrackerSubsystem("sub_event_listener", TickStage.POST_TICK_MAINTENANCE, priority=10)
        self.engine.register_subsystem(custom_sub)

        test_evt = DomainEvent(
            event_type="test_custom_announcement",
            tick=1,
            source_id="unit_test",
            payload={"msg": "Hello Subsystems"}
        )
        self.engine.pipeline_manager.broadcast_event(test_evt, self.engine.context)

        self.assertIn("test_custom_announcement", custom_sub.received_events)

    def test_08_subsystem_state_snapshot_roundtrip(self):
        """Verify that subsystem states are serialized and restored correctly in engine snapshots."""
        custom_sub = MockExecutionTrackerSubsystem("sub_stateful", TickStage.PRE_TICK, priority=10)
        self.engine.register_subsystem(custom_sub)
        self.engine.tick(count=5)
        self.assertEqual(custom_sub.custom_state, 105)

        # Save snapshot
        snapshot = self.engine.save_snapshot()
        self.assertIn("subsystem_states", snapshot)
        self.assertIn("sub_stateful", snapshot["subsystem_states"])
        self.assertEqual(snapshot["subsystem_states"]["sub_stateful"]["custom_state"], 105)

        # Mutate state, then load snapshot
        custom_sub.custom_state = 999
        self.engine.load_snapshot(snapshot)
        self.assertEqual(custom_sub.custom_state, 105)


if __name__ == "__main__":
    unittest.main()
