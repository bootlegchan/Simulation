"""Unit Test Suite 01: Core Infrastructure Primitives."""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir, get_project_root
from src.core.clock import SimulationClock
from src.core.randomness import SeededRandom
from src.core.events import EventBus, DomainEvent
from src.core.event_sourcing import EventStore
from src.core.errors import LifecycleError
from src.configuration.loader import ContentLoader

class TestCoreAndInfrastructure(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()

    def test_path_utils_dynamic_resolution(self):
        root = get_project_root()
        data = get_default_data_dir()
        self.assertTrue(root.exists())
        self.assertTrue(data.exists())

    def test_clock_operations_and_iso_format(self):
        clock = SimulationClock(start_time_iso="2026-01-01T06:00:00Z", ticks_per_minute=1)
        self.assertTrue(clock.is_paused)
        with self.assertRaises(LifecycleError):
            clock.advance_tick(1)
        clock.resume()
        self.assertFalse(clock.is_paused)
        tick = clock.advance_tick(60)
        self.assertEqual(tick, 60)
        self.assertIn("2026-01-01T07:00:00", clock.current_virtual_time_iso)

    def test_seeded_random_bitwise_reproducibility(self):
        rand1 = SeededRandom(seed=42)
        rand2 = SeededRandom(seed=42)
        seq1 = [rand1.random() for _ in range(50)]
        seq2 = [rand2.random() for _ in range(50)]
        self.assertEqual(seq1, seq2)

    def test_event_bus_and_event_store(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda e: received.append(e))
        bus.publish(DomainEvent("test_event", tick=1, source_id="test", payload={"key": "val"}))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["key"], "val")

        store = EventStore()
        store.append(DomainEvent("action", tick=1, source_id="npc1"))
        self.assertEqual(len(store.get_events_for_tick(1)), 1)

    def test_content_loader_basic(self):
        loader = ContentLoader(self.data_dir)
        data = loader.load_content("oakwood_baseline.json")
        self.assertIn("settlements", data)
        self.assertIn("npcs", data)
        self.assertIn("items", data)

if __name__ == "__main__":
    unittest.main()
