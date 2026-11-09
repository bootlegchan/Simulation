"""Unit Suite 92: Data Layer, Connector Live Queries, Telemetry, and Explainable Agency Facade."""
import unittest
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.api.local_interface import SimulationConnector, LocalVisualAPI
from src.diagnostics.live_telemetry import LiveTelemetryEngine
from src.diagnostics.deep_simulation_reporter import DeepSimulationReporter
from src.diagnostics.simulation_integrity import SimulationIntegrityAuditor
from src.core.events import DomainEvent

class TestDataLayerConnectorTelemetryAndExplainability(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.connector = self.engine.get_connector()
        self.api = self.engine.get_visual_api()

    def test_01_connector_live_commodity_and_economic_queries(self):
        """Verify SimulationConnector queries live services, not hardcoded dummy stubs."""
        # Step simulation to initiate production
        self.engine.tick(60)

        # 1. Commodity stocks from supply chain
        stocks = self.connector.get_commodity_stocks()
        self.assertIsInstance(stocks, dict)
        self.assertIn("raw_wheat", stocks)
        self.assertIn("flour", stocks)
        self.assertIn("food_bread", stocks)

        # 2. Market prices
        prices = self.connector.get_commodity_prices()
        self.assertIsInstance(prices, dict)
        self.assertGreater(prices.get("food_bread", 0.0), 0.0)

        # 3. Factions
        factions = self.connector.get_faction_statuses()
        self.assertIsInstance(factions, dict)
        self.assertGreaterEqual(len(factions), 1)

        # 4. Household finances
        hh = self.connector.get_household_finances()
        self.assertIsInstance(hh, list)
        self.assertGreaterEqual(len(hh), 1)
        first_hh = hh[0]
        self.assertIn("household_id", first_hh)
        self.assertIn("aggregate_wealth_gold", first_hh)

    def test_02_live_telemetry_engine_real_time_metrics_and_timeseries(self):
        """Verify LiveTelemetryEngine records dynamic live snapshots and extracts timeseries."""
        telemetry = LiveTelemetryEngine()
        self.engine.tick(30)
        s1 = telemetry.record_tick(self.engine)
        self.engine.tick(30)
        s2 = telemetry.record_tick(self.engine)

        self.assertGreaterEqual(s1["demographics"]["alive_count"], 40)
        self.assertGreater(s1["economy"]["total_currency_gold"], 0.0)
        self.assertIn("avg_contentment", s1["psychology"])

        # Timeseries query
        ts = telemetry.get_metric_timeseries("avg_contentment", limit=5)
        self.assertEqual(len(ts), 2)
        self.assertIn("value", ts[0])

        # Nested timeseries query
        ts_curr = telemetry.get_metric_timeseries("economy.total_currency_gold", limit=5)
        self.assertEqual(len(ts_curr), 2)

    def test_03_deep_simulation_reporter_comprehensive_dossier(self):
        """Verify DeepSimulationReporter captures initial baseline and synthesizes populated report."""
        reporter = DeepSimulationReporter()
        reporter.capture_initial_baseline(self.engine.context)
        self.engine.tick(60)
        report = reporter.generate_report_data(self.engine.context)

        self.assertIn("demographics", report)
        self.assertIn("psychology", report)
        self.assertIn("economy", report)
        self.assertIn("governance_and_justice", report)
        self.assertIn("information_and_kinship", report)
        self.assertIn("means_end_volition", report)

        # Verify populated feelings summary
        feelings = report["psychology"]["feelings_summary"]
        self.assertIn("contentment", feelings)
        self.assertIn("mean", feelings["contentment"])

    def test_04_subsystem_profiler_and_timing_instrumentation(self):
        """Verify SubsystemPipelineManager tracks execution durations, call counts, and errors."""
        self.engine.tick(60)
        profile = self.engine.pipeline_manager.get_performance_profile()

        self.assertIn("subsystem_timings_ms", profile)
        self.assertIn("subsystem_call_counts", profile)
        self.assertIn("avg_tick_duration_ms", profile)

        # Cognitive subsystem should have execution time and call counts
        self.assertIn("subsystem_cognitive", profile["subsystem_timings_ms"])
        self.assertGreater(profile["subsystem_call_counts"]["subsystem_cognitive"], 0)

    def test_05_event_bus_browser_streaming_and_entity_timelines(self):
        """Verify EventBus supports live stream offsets, filtering, and entity audit trails."""
        bus = self.engine.event_bus
        bus.clear()

        t0 = 100.0
        e1 = DomainEvent("crime_occurred", tick=10, source_id="npc_tobias", payload={"victim_id": "npc_greta"}, timestamp=t0 + 1.0)
        e2 = DomainEvent("food_purchased", tick=12, source_id="npc_aldous", payload={"cost_gold": 1.2}, timestamp=t0 + 2.0)
        e3 = DomainEvent("lawsuit_filed", tick=15, source_id="court", payload={"defendant_id": "npc_tobias"}, timestamp=t0 + 3.0)

        bus.publish(e1)
        bus.publish(e2)
        bus.publish(e3)

        # 1. Stream since timestamp
        stream = bus.get_stream(since_timestamp=t0 + 1.5)
        self.assertEqual(len(stream), 2)
        self.assertEqual(stream[0]["event_type"], "food_purchased")

        # 2. Query by entity timeline for npc_tobias
        tobias_timeline = bus.get_entity_timeline("npc_tobias")
        self.assertEqual(len(tobias_timeline), 2)
        self.assertIn(tobias_timeline[0]["event_type"], ("crime_occurred", "lawsuit_filed"))

    def test_06_local_visual_api_world_and_room_inspection(self):
        """Verify LocalVisualAPI exposes architectural hierarchy and rich room inspection."""
        hierarchy = self.api.get_world_hierarchy()
        self.assertIn("settlement_oakwood", hierarchy)

        room_info = self.api.get_room_details("room_bakery")
        self.assertEqual(room_info["room_id"], "room_bakery")
        self.assertIn("occupants", room_info)
        self.assertIn("connected_rooms", room_info)

        # Graph integrity verification
        integrity = self.api.verify_world_integrity()
        self.assertTrue(integrity["is_valid"])

    def test_07_local_visual_api_citizen_deep_inspection_and_decision_explanation(self):
        """Verify LocalVisualAPI provides explainable agency: utilities, dominant thoughts, and relationships."""
        self.engine.tick(60)

        # 1. Citizen Profile & State
        profile = self.api.get_citizen_profile("npc_aldous")
        self.assertEqual(profile["id"], "npc_aldous")
        self.assertIn("personality_ocean", profile)

        state = self.api.get_citizen_state("npc_aldous")
        self.assertIn("needs", state)
        self.assertIn("feelings", state)

        # 2. Explainable Agency Decision Explanation
        exp = self.api.get_citizen_decision_explanation("npc_aldous")
        self.assertEqual(exp["npc_id"], "npc_aldous")
        self.assertIn("chosen_drive", exp)
        self.assertIn("all_drive_utilities", exp)
        self.assertIn("working_memory_spotlight", exp)
        self.assertIn("desire_hierarchy", exp)

        # 3. Relationships & Epistemic Knowledge
        rel = self.api.get_citizen_relationships("npc_aldous")
        self.assertIn("romantic_bond", rel)
        self.assertIn("opinions", rel)

        know = self.api.get_citizen_knowledge("npc_aldous")
        self.assertIn("memory_traces", know)

        # 4. History
        hist = self.api.get_citizen_history("npc_aldous")
        self.assertIn("career_stats", hist)
        self.assertIn("biographical_log", hist)

    def test_08_local_visual_api_controls_and_content_management(self):
        """Verify LocalVisualAPI step, fast-forward, pause/resume, and settings inspection."""
        stat_init = self.api.get_simulation_status()
        init_tick = stat_init["tick"]

        # Step
        stat_step = self.api.step(10)
        self.assertEqual(stat_step["tick"], init_tick + 10)

        # Fast-forward
        stat_ff = self.api.fast_forward(30)
        self.assertEqual(stat_ff["tick"], init_tick + 40)

        # Pause & Resume
        p_stat = self.api.pause()
        self.assertTrue(p_stat["is_paused"])
        r_stat = self.api.resume()
        self.assertFalse(r_stat["is_paused"])

        # Content inspection
        packs = self.api.get_content_packs()
        self.assertIsInstance(packs, list)

        phys_cfg = self.api.inspect_settings_manifest("physiology")
        self.assertIn("sleep_recovery", phys_cfg)

        patch_prev = self.api.preview_merge_patch({"physiology": {"sleep_recovery": {"energy_gain_per_hour": 16.0}}})
        self.assertTrue(patch_prev["valid"])

if __name__ == "__main__":
    unittest.main()
