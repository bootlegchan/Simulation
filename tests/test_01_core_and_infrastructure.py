"""
Consolidated Test Suite 01: Core Infrastructure, Clock, Randomness, Events, and Configuration.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir, get_project_root
from src.core.clock import SimulationClock
from src.core.randomness import SeededRandom
from src.core.events import EventBus, DomainEvent
from src.core.event_sourcing import EventStore
from src.core.errors import LifecycleError
from src.configuration.loader import ContentLoader
from src.configuration.validator import SchemaValidator


class TestCoreAndInfrastructure(unittest.TestCase):
    """Verifies core system primitives: Clock, SeededRandom, EventBus, Pathing, and Loader."""

    def setUp(self):
        self.data_dir = get_default_data_dir()

    def test_path_utils_dynamic_resolution(self):
        root = get_project_root()
        data = get_default_data_dir()
        self.assertTrue(root.exists())
        self.assertTrue(data.exists())
        self.assertEqual(data, root / "data")

    def test_clock_operations_and_iso_format(self):
        clock = SimulationClock(start_time_iso="2026-01-01T06:00:00Z", ticks_per_minute=1)
        self.assertTrue(clock.is_paused)

        with self.assertRaises(LifecycleError):
            clock.advance_tick(1)

        clock.resume()
        self.assertFalse(clock.is_paused)

        tick = clock.advance_tick(60)
        self.assertEqual(tick, 60)
        self.assertEqual(clock.current_virtual_time_iso, "2026-01-01T07:00:00+00:00")

        clock_dict = clock.to_dict()
        clock_restored = SimulationClock.from_dict(clock_dict)
        self.assertEqual(clock_restored.current_tick, 60)

    def test_seeded_random_bitwise_reproducibility(self):
        rand1 = SeededRandom(seed=42)
        rand2 = SeededRandom(seed=42)

        sequence1 = [rand1.random() for _ in range(100)]
        sequence2 = [rand2.random() for _ in range(100)]
        self.assertEqual(sequence1, sequence2)

        roll1 = rand1.randint(1, 100)
        roll2 = rand2.randint(1, 100)
        self.assertEqual(roll1, roll2)

        # Snapshot and restoration check
        snap = rand1.to_dict()
        val_before = rand1.random()
        rand3 = SeededRandom.from_dict(snap)
        val_after = rand3.random()
        self.assertEqual(val_before, val_after)

    def test_event_bus_and_event_store(self):
        bus = EventBus()
        received_events = []

        def subscriber(evt: DomainEvent):
            received_events.append(evt)

        bus.subscribe("test_event", subscriber)
        bus.publish(DomainEvent("test_event", tick=1, source_id="unit_test", payload={"key": "val"}))

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].payload["key"], "val")
        self.assertEqual(len(bus.history), 1)

        # Event Store
        store = EventStore()
        evt1 = DomainEvent("npc_action", tick=1, source_id="npc_1", payload={"action": "eat"})
        evt2 = DomainEvent("npc_action", tick=2, source_id="npc_1", payload={"action": "sleep"})
        store.append(evt1)
        store.append(evt2)

        tick_events = store.get_events_for_tick(1)
        self.assertEqual(len(tick_events), 1)
        self.assertEqual(tick_events[0].payload["action"], "eat")

    def test_content_loader_and_schema_validation(self):
        loader = ContentLoader(self.data_dir)
        data = loader.load_content("oakwood_baseline.json")

        self.assertIn("settlements", data)
        self.assertIn("npcs", data)
        self.assertIn("objects", data)
        self.assertIn("items", data)

        if "npc" in loader.schemas:
            aldous_data = list(data["npcs"].values())[0]
            val_res = SchemaValidator.validate(aldous_data, loader.schemas["npc"])
            self.assertTrue(val_res)


if __name__ == "__main__":
    unittest.main()
