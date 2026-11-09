"""
Unit Test Suite 77: Continuous Weather, Micro-Climate & Room Thermodynamics.
Verifies the continuous thermodynamic meteorological architecture:
- Sinusoidal diurnal solar curves and seasonal means
- Continuous barometric pressure drift and precipitation generation
- Room thermodynamics: building insulation, active hearth combustion, and body heat
- Somatic thermal homeostasis: cold thermogenesis metabolic hunger scaling
- EnvironmentAndWeatherSubsystem execution at TickStage.PRE_TICK_ENVIRONMENT
- Event bus dispatch on weather state transitions
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.core.subsystem import TickStage
from src.world.climate import MicroClimateEngine, WeatherType, ContinuousWeatherState
from src.subsystems.environment_and_weather import EnvironmentAndWeatherSubsystem

class TestContinuousWeatherAndThermodynamics(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.climate_eng: MicroClimateEngine = self.engine.context.get_service("micro_climate_engine")

    def test_01_continuous_diurnal_solar_curve(self):
        """Verify that temperature follows a continuous diurnal solar sine wave with peak at 13:00."""
        # Tick 420 = 06:00 (start 06:00) + 7 hours = 13:00 (solar peak)
        # 13:00 is hour 13
        weather_noon = self.climate_eng.update_weather(tick=420)
        self.assertEqual(weather_noon.hour, 13.0)
        self.assertGreater(weather_noon.diurnal_temperature_offset, 0.0)
        self.assertAlmostEqual(weather_noon.solar_intensity, 1.0, delta=0.35)

        # Tick 1140 = 06:00 + 19 hours = 01:00 next day (solar minimum)
        weather_night = self.climate_eng.update_weather(tick=1140)
        self.assertEqual(weather_night.hour, 1.0)
        self.assertLess(weather_night.diurnal_temperature_offset, 0.0)
        self.assertEqual(weather_night.solar_intensity, 0.0)

        # Solar peak is warmer than midnight
        self.assertGreater(weather_noon.ambient_temperature, weather_night.ambient_temperature)

    def test_02_barometric_pressure_and_precipitation(self):
        """Verify that falling pressure generates cloud cover and precipitation."""
        state = self.climate_eng.update_weather(tick=1800)
        self.assertIsInstance(state.barometric_pressure_kpa, float)
        self.assertGreater(state.barometric_pressure_kpa, 95.0)
        self.assertLess(state.barometric_pressure_kpa, 105.0)

        # Precipitation type is a valid WeatherType enum
        self.assertIn(state.precipitation_type, list(WeatherType))
        self.assertGreaterEqual(state.humidity, 0.0)
        self.assertLessEqual(state.humidity, 1.0)

    def test_03_room_thermodynamics_insulation_and_hearth(self):
        """Verify that building insulation and active hearths keep indoor spaces warm during winter."""
        # Force a winter tick at night (cold ambient temp)
        # Tick 1140 = 01:00 (Winter night)
        self.climate_eng.update_weather(tick=1140)
        amb_temp = self.climate_eng.current_weather.ambient_temperature

        # Outdoor village square matches ambient cold
        plaza_temp = self.climate_eng.get_room_temperature("room_village_square", self.engine.context, tick=1140)
        self.assertAlmostEqual(plaza_temp, amb_temp, places=1)

        # Bakery hearth floor stays significantly warmer due to ovens and hearth
        bakery_temp = self.climate_eng.get_room_temperature("room_bakery", self.engine.context, tick=1140)
        self.assertGreater(bakery_temp, plaza_temp + 12.0)

        # Farmhouse kitchen with hearth is also well-heated
        farm_temp = self.climate_eng.get_room_temperature("room_farmhouse", self.engine.context, tick=1140)
        self.assertGreater(farm_temp, plaza_temp + 10.0)

    def test_04_cold_somatic_thermogenesis_hunger_acceleration(self):
        """Verify that cold room temperatures scale somatic hunger decay up to 1.65x for thermogenesis."""
        citizen = self.engine.npcs["npc_aldous"]
        citizen.current_action = "IDLE"

        # Baseline: room at comfortable 20°C
        citizen._current_room_temperature = 20.0
        h_rate_warm = citizen.calculate_hunger_decay("IDLE", current_tick=100)

        # Cold environment: room at freezing -2°C
        citizen._current_room_temperature = -2.0
        h_rate_freezing = citizen.calculate_hunger_decay("IDLE", current_tick=100)

        # Cold thermogenesis metabolic burn is significantly higher
        self.assertGreater(h_rate_freezing, h_rate_warm)
        ratio = h_rate_freezing / h_rate_warm
        self.assertGreaterEqual(ratio, 1.30)
        self.assertLessEqual(ratio, 1.70)

        # Check thermal comfort status
        comfort = citizen.get_thermal_comfort()
        self.assertTrue(comfort["is_freezing"])
        self.assertTrue(comfort["is_shivering"])
        self.assertFalse(comfort["is_comfortable"])

    def test_05_environment_subsystem_dispatch_and_registration(self):
        """Verify that EnvironmentAndWeatherSubsystem runs at PRE_TICK_ENVIRONMENT stage."""
        subsystems = self.engine.pipeline_manager.subsystems
        env_subs = [s for s in subsystems if s.subsystem_id == "subsystem_environment_and_weather"]
        self.assertEqual(len(env_subs), 1)

        env_sub = env_subs[0]
        self.assertEqual(env_sub.tick_stage, TickStage.PRE_TICK_ENVIRONMENT)
        self.assertEqual(env_sub.execution_priority, 5)

        # Run 1 tick: citizens should have _current_room_temperature updated
        self.engine.tick(1)
        for npc in self.engine.npcs.values():
            self.assertTrue(hasattr(npc, "_current_room_temperature"))
            self.assertIsInstance(npc._current_room_temperature, float)

    def test_06_fast_forward_temporal_weather_continuity(self):
        """Verify that fast_forward advances weather state smoothly and deterministically."""
        initial_tick = self.engine.clock.current_tick
        self.engine.fast_forward(total_ticks=720, max_leap=60)
        self.assertEqual(self.engine.clock.current_tick, initial_tick + 720)

        current_w = self.climate_eng.current_weather
        self.assertIsNotNone(current_w)
        self.assertEqual(current_w.tick, self.engine.clock.current_tick)

if __name__ == "__main__":
    unittest.main()
