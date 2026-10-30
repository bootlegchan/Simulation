"""
Consolidated Test Suite 07: Portability, REST & WebSocket API, Visual DTOs, and Real-Time Runner.
"""
import time
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from src.core.path_utils import get_default_data_dir, get_project_root
from src.simulation.engine import SimulationEngine
from src.simulation.runner import SimulationRunner
from src.api.router import create_app
from src.api.dtos import SimulationTickBatchDTO
from src.api.bridge import StateMutator, BridgeRPCCommandDTO


class TestAPIAndRealtimeRunner(unittest.TestCase):
    """Verifies Portability, REST & WebSocket Endpoints, Visual DTO Projections, Real-Time Runner, and State Mutation Interface."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=2026)
        self.runner = SimulationRunner(self.engine, target_tps=50.0)
        self.app = create_app(self.engine, self.runner)
        self.client = TestClient(self.app)

    def tearDown(self):
        if self.runner.is_running:
            self.runner.stop_live_runner()

    def test_api_status_control_and_spatial_projections(self):
        res_status = self.client.get("/api/v1/simulation/status")
        self.assertEqual(res_status.status_code, 200)
        status_data = res_status.json()
        self.assertIn("virtual_time_iso", status_data)

        # Control step 5 ticks
        res_ctrl = self.client.post("/api/v1/simulation/control", json={"action": "step", "step_ticks": 5})
        self.assertEqual(res_ctrl.status_code, 200)

        # Spatial Graph DTO
        res_graph = self.client.get("/api/v1/spatial/graph")
        self.assertEqual(res_graph.status_code, 200)
        graph = res_graph.json()
        self.assertIn("nodes", graph)

        # NPC Visual DTOs
        res_npcs = self.client.get("/api/v1/npcs")
        self.assertEqual(res_npcs.status_code, 200)
        npcs = res_npcs.json()
        self.assertIn("npc_aldous", npcs)

    def test_realtime_simulation_runner_and_subscribers(self):
        batches = []

        def subscriber_cb(batch: SimulationTickBatchDTO):
            batches.append(batch)

        self.runner.register_subscriber(subscriber_cb)

        initial_tick = self.engine.clock.current_tick if self.engine.clock else 0
        initial_hunger = self.engine.npcs["npc_aldous"].needs.get("hunger", 0.0)

        self.runner.start_live_runner()
        self.assertTrue(self.runner.is_running)

        time.sleep(0.2)  # Active run

        self.runner.stop_live_runner()
        self.assertFalse(self.runner.is_running)

        final_tick = self.engine.clock.current_tick if self.engine.clock else 0
        final_hunger = self.engine.npcs["npc_aldous"].needs.get("hunger", 0.0)

        self.assertGreater(final_tick, initial_tick)
        self.assertGreater(len(batches), 0)
        self.assertGreater(final_hunger, initial_hunger)

    def test_api_state_mutation_endpoints_and_rpc_bridge(self):
        # REST Mutate NPC
        res_mutate = self.client.post("/api/v1/mutate/npc/npc_aldous", json={"wealth": 250.0, "needs": {"hunger": 10.0}})
        self.assertEqual(res_mutate.status_code, 200)
        self.assertEqual(self.engine.npcs["npc_aldous"].wealth, 250.0)

        # REST Force Action
        res_action = self.client.post("/api/v1/mutate/npc/npc_aldous/action", json={"action_type": "WORK"})
        self.assertEqual(res_action.status_code, 200)

        # WebSocket RPC Bridge Mutation Command
        cmd = BridgeRPCCommandDTO(command_id="cmd_1", command_type="MUTATE_NPC", target_id="npc_aldous", payload={"wealth": 500.0})
        resp = StateMutator.execute_rpc_command(self.engine, cmd)

        self.assertTrue(resp.success)
        self.assertEqual(self.engine.npcs["npc_aldous"].wealth, 500.0)


if __name__ == "__main__":
    unittest.main()
