"""Unit tests for the immersive presentation bridge."""
import math
import unittest
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from frontend_bridge.server import build_snapshot,to_json_value,validate_ticks


class Sample(Enum):
    READY = "READY"


@dataclass
class SampleRecord:
    name: str
    count: int


class SerializationTests(unittest.TestCase):
    def test_known_values_become_json_primitives(self):
        result = to_json_value({"state":Sample.READY,"path":Path("data/a.json"),
                                "record":SampleRecord("square",3),"items":(1,2),"nan":math.nan})
        self.assertEqual(result["state"],"READY")
        self.assertEqual(result["path"],"data/a.json")
        self.assertEqual(result["record"],{"name":"square","count":3})
        self.assertEqual(result["items"],[1,2])
        self.assertIsNone(result["nan"])

    def test_unknown_values_and_excessive_nesting_are_rejected(self):
        with self.assertRaises(TypeError):
            to_json_value(object())
        nested = None
        for _ in range(34):
            nested = [nested]
        with self.assertRaises(ValueError):
            to_json_value(nested)


class ValidationTests(unittest.TestCase):
    def test_tick_validation(self):
        self.assertEqual(validate_ticks(None),1)
        self.assertEqual(validate_ticks(50),50)
        for invalid in (True,0,100001,"2"):
            with self.assertRaises(ValueError):
                validate_ticks(invalid)


class SnapshotTests(unittest.TestCase):
    def test_snapshot_uses_facade_and_engine_state(self):
        api = Mock()
        api.API_VERSION = "test-api"
        api.get_room_details.return_value = {"room_id":"room_village_square"}
        api.get_simulation_status.return_value = {"tick":12,"lifecycle_state":"RUNNING"}
        api.get_climate_status.return_value = {"precipitation":"CLEAR"}
        api.get_economy_overview.return_value = {"treasury_balance_gold":10}
        api.get_world_hierarchy.return_value = {"settlement_oakwood":{}}
        api.get_spatial_connections.return_value = []
        api.list_citizens.return_value = [{"id":"npc_1","location_id":"room_village_square"}]
        room = SimpleNamespace(id="room_village_square")
        building = SimpleNamespace(rooms={"room_village_square":room})
        settlement = SimpleNamespace(buildings={"building":building})
        engine = SimpleNamespace(settlements={"settlement":settlement},objects={},
            npcs={"npc_1":SimpleNamespace(is_alive=True)},
            context=SimpleNamespace(get_service=lambda _name:object()))
        snapshot = build_snapshot(api,engine,"room_village_square")
        self.assertEqual(snapshot["schema_version"],"1.0")
        self.assertEqual(snapshot["status"]["tick"],12)
        self.assertEqual(snapshot["active_room"]["room_id"],"room_village_square")
        self.assertEqual(snapshot["npcs"][0]["id"],"npc_1")
        self.assertTrue(snapshot["climate"]["data_quality"]["weather_available"])


if __name__ == "__main__":
    unittest.main()
