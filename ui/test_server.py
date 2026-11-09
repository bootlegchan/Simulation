"""Unit tests for the Oakwood local HTTP adapter."""
import math
import unittest
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from ui.server import ApiError, OakwoodHandler, to_json_value


class SampleState(Enum):
    READY = "READY"


class AdapterSerializationTests(unittest.TestCase):
    def test_serializes_common_python_values(self):
        value = {
            "state": SampleState.READY,
            "time": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "path": Path("data/scenarios/example.json"),
            "finite": 2.5,
            "not_finite": math.nan,
            "items": (1, 2),
        }
        result = to_json_value(value)
        self.assertEqual(result["state"], "READY")
        self.assertEqual(result["time"], "2026-01-02T00:00:00+00:00")
        self.assertEqual(result["path"], "data/scenarios/example.json")
        self.assertEqual(result["finite"], 2.5)
        self.assertIsNone(result["not_finite"])
        self.assertEqual(result["items"], [1, 2])

    def test_rejects_excessively_nested_values(self):
        value = None
        for _ in range(35):
            value = [value]
        with self.assertRaises(ValueError):
            to_json_value(value)

    def test_tick_validation_rejects_bool_and_out_of_range(self):
        with self.assertRaises(ApiError):
            OakwoodHandler._int_arg(True, "ticks", 1, 1, 100)
        with self.assertRaises(ApiError):
            OakwoodHandler._int_arg(101, "ticks", 1, 1, 100)
        self.assertEqual(OakwoodHandler._int_arg(5, "ticks", 1, 1, 100), 5)


class AdapterDispatchTests(unittest.TestCase):
    def setUp(self):
        self.handler = object.__new__(OakwoodHandler)
        self.handler.api = Mock()
        self.handler.engine = SimpleNamespace(
            npcs={"a": SimpleNamespace(is_alive=True), "b": SimpleNamespace(is_alive=False)},
            context=SimpleNamespace(get_service=lambda name: object() if name == "micro_climate_engine" else None),
        )

    def test_status_includes_population_and_weather_source(self):
        self.handler.api.get_simulation_status.return_value = {"tick": 7}
        result = self.handler._dispatch_get("/simulation/status", {})
        self.assertEqual(result["population"], 1)
        self.assertEqual(result["total_population"], 2)
        self.assertTrue(result["data_quality"]["weather_available"])

    def test_climate_response_marks_source_availability(self):
        self.handler.api.get_climate_status.return_value = {"season": "SPRING"}
        result = self.handler._dispatch_get("/climate/status", {})
        self.assertTrue(result["data_quality"]["weather_available"])

    def test_citizen_list_passes_filters_to_facade(self):
        self.handler.api.list_citizens.return_value = []
        self.handler._dispatch_get("/citizens", {"role": ["baker"], "alive_only": ["false"]})
        self.handler.api.list_citizens.assert_called_once_with(filter_role="baker", alive_only=False)

    def test_step_command_is_bounded_and_calls_facade(self):
        self.handler.api.step.return_value = {"tick": 4}
        result = self.handler._dispatch_post("/simulation/step", {"ticks": 4})
        self.assertEqual(result, {"tick": 4})
        self.handler.api.step.assert_called_once_with(4)
        with self.assertRaises(ApiError):
            self.handler._dispatch_post("/simulation/step", {"ticks": 100001})

    def test_reset_rejects_path_traversal(self):
        with self.assertRaises(ApiError):
            self.handler._dispatch_post("/simulation/reset", {"scenario_filename": "../outside.json"})


if __name__ == "__main__":
    unittest.main()
