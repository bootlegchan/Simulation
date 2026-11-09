"""
Unit Test Suite 78: Commodity Production & Physical Supply Chains.
Verifies the production engine at TickStage.ECONOMIC_PRODUCTION:
- Declarative recipes and multi-stage supply chains
- Physical material transformation (input consumption, output deposition)
- Quality scaling based on artisan skill
- Weather-modulated agricultural yields (beneficial rain vs freezing frost)
- Continuous supply-demand price elasticity
- Autonomous subsystem execution during economic production stage
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.core.subsystem import TickStage
from src.economy.supply_chain import CommoditySupplyChainEngine
from src.behaviours.actions import ActionRegistry

class TestCommodityProductionAndSupplyChains(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.sc_eng: CommoditySupplyChainEngine = self.engine.context.get_service("supply_chain_engine")
        self.sc_eng.reseed_stocks()

    def test_01_supply_chain_engine_initialization_and_registration(self):
        """Verify that CommoditySupplyChainEngine is registered and tracks initial stocks."""
        self.assertIsNotNone(self.sc_eng)
        self.assertGreater(self.sc_eng.get_stock_level("raw_wheat"), 0.0)
        self.assertGreater(self.sc_eng.get_stock_level("flour"), 0.0)
        self.assertGreater(self.sc_eng.get_stock_level("food_bread"), 0.0)

        # Check subsystem registration in pipeline
        registered_subs = [
            s for s in self.engine.pipeline_manager.subsystems
            if s.subsystem_id == "subsystem_commodity_production"
        ]
        self.assertEqual(len(registered_subs), 1)
        sub = registered_subs[0]
        self.assertEqual(sub.tick_stage, TickStage.ECONOMIC_PRODUCTION)

    def test_02_physical_material_transformation_inputs_and_outputs(self):
        """Verify that executing a crafting recipe consumes inputs and deposits outputs."""
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"
        baker.location_id = "room_bakery"

        # Record initial stocks
        init_flour = self.sc_eng.get_stock_level("flour")
        init_bread = self.sc_eng.get_stock_level("food_bread")

        res = self.sc_eng.execute_production_step(baker, "bake_bread", self.engine.context, tick=60)
        self.assertTrue(res["success"])
        self.assertIn("food_bread", res["outputs_produced"])

        # Flour was consumed (-1.0), Bread was produced (+3.0)
        self.assertEqual(self.sc_eng.get_stock_level("flour"), init_flour - 1.0)
        self.assertEqual(self.sc_eng.get_stock_level("food_bread"), init_bread + 3.0)

        # Career statistic logged
        self.assertGreaterEqual(baker.career_statistics.get("goods_crafted_count", 0), 1)

    def test_03_quality_scaling_based_on_artisan_skill(self):
        """Verify that crafted item quality scales continuously with worker skill rating."""
        master_smith = self.engine.npcs["npc_aldous"]
        master_smith.skills["smithing"] = 90.0

        novice_smith = self.engine.npcs["npc_citizen_01"]
        novice_smith.skills["smithing"] = 15.0

        # Provide sufficient ore
        self.sc_eng.add_stock("raw_iron_ore", 20.0)

        res_master = self.sc_eng.execute_production_step(master_smith, "smelt_iron", self.engine.context, tick=100)
        res_novice = self.sc_eng.execute_production_step(novice_smith, "smelt_iron", self.engine.context, tick=100)

        self.assertTrue(res_master["success"])
        self.assertTrue(res_novice["success"])
        self.assertGreater(res_master["quality"], res_novice["quality"])
        self.assertGreaterEqual(res_master["quality"], 1.10)

    def test_04_weather_sensitive_agricultural_yields(self):
        """Verify that agrarian yields scale with weather (favorable rain vs freezing frost)."""
        farmer = self.engine.npcs["npc_aldous"]
        farmer.occupation = "Agrarian Farmer"
        farmer.location_id = "room_farmhouse"

        clim_eng = self.engine.context.get_service("micro_climate_engine")
        self.assertIsNotNone(clim_eng)

        # Scenario A: Freezing frost condition (-4°C)
        clim_eng.update_weather(100) # Winter tick
        clim_eng.current_weather.ambient_temperature = -4.0
        clim_eng.current_weather.precipitation_intensity = 0.0

        res_freeze = self.sc_eng.execute_production_step(farmer, "harvest_wheat", self.engine.context, tick=100)
        self.assertTrue(res_freeze["success"])
        self.assertEqual(res_freeze["weather_multiplier"], 0.65) # Frost penalty!

        # Scenario B: Favorable warm rain condition (+15°C, rain = 0.35)
        clim_eng.current_weather.ambient_temperature = 15.0
        clim_eng.current_weather.precipitation_intensity = 0.35

        res_rain = self.sc_eng.execute_production_step(farmer, "harvest_wheat", self.engine.context, tick=200)
        self.assertTrue(res_rain["success"])
        self.assertEqual(res_rain["weather_multiplier"], 1.25) # Rain boom!
        self.assertGreater(res_rain["outputs_produced"]["raw_wheat"], res_freeze["outputs_produced"]["raw_wheat"])

    def test_05_continuous_supply_demand_price_elasticity(self):
        """Verify continuous price elasticity: high stock drops price, scarcity spikes price."""
        self.sc_eng.reseed_stocks()
        # Baseline price of food_bread is 1.20, target stock is 30
        p_normal = self.sc_eng.calculate_market_price("food_bread")
        self.assertAlmostEqual(p_normal, 1.20, delta=0.25)

        # Scarcity: Stock drops to 5 units
        self.sc_eng.commodity_stocks["food_bread"] = 5.0
        p_scarce = self.sc_eng.calculate_market_price("food_bread")
        self.assertGreater(p_scarce, p_normal)

        # Abundance: Stock rises to 100 units
        self.sc_eng.commodity_stocks["food_bread"] = 100.0
        p_abundant = self.sc_eng.calculate_market_price("food_bread")
        self.assertLess(p_abundant, p_normal)

    def test_06_subsystem_dispatch_during_economic_production_stage(self):
        """Verify that CommodityProductionSubsystem processes active artisans during Stage 4."""
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"
        baker.current_action = "LABOR_WORK"
        baker.location_id = "room_bakery"

        init_bread = self.sc_eng.get_stock_level("food_bread")
        self.sc_eng.add_stock("flour", 10.0)

        # Run 1 cycle of commodity production subsystem at tick 60
        prod_sub = [
            s for s in self.engine.pipeline_manager.subsystems
            if s.subsystem_id == "subsystem_commodity_production"
        ][0]
        prod_sub.on_tick(60, self.engine.context)

        # Bread was produced by the working baker!
        self.assertGreater(self.sc_eng.get_stock_level("food_bread"), init_bread)

if __name__ == "__main__":
    unittest.main()
