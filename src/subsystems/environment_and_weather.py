"""
Environment and Weather Subsystem.
Executes at TickStage.PRE_TICK_ENVIRONMENT (priority 5).
Manages continuous meteorological conditions (solar diurnal curve, barometric drift,
precipitation) and computes room thermodynamics across settlements.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.world.climate import MicroClimateEngine, ContinuousWeatherState, WeatherType

class EnvironmentAndWeatherSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_environment_and_weather"
    name = "Environment and Weather Subsystem"
    tick_stage = TickStage.PRE_TICK_ENVIRONMENT
    tick_frequency = 1
    execution_priority = 5
    is_enabled = True

    def __init__(self):
        self.climate_engine = MicroClimateEngine.get_instance()
        self._last_weather_type: Optional[WeatherType] = None

    def initialize(self, context: WorldContext) -> None:
        context.register_service("micro_climate_engine", self.climate_engine)
        context.register_service("weather_and_climate_engine", self.climate_engine)
        # Initialize initial weather state at tick 0
        state = self.climate_engine.update_weather(0, context)
        self._last_weather_type = state.precipitation_type

    def on_tick(self, tick: int, context: WorldContext) -> None:
        # 1. Update Continuous Meteorological Field
        state = self.climate_engine.update_weather(tick, context)

        # 2. Check for Weather Shift Events
        if self._last_weather_type != state.precipitation_type:
            context.publish_event(
                event_type="WEATHER_STATE_CHANGED",
                source_id="subsystem_environment_and_weather",
                payload=state.to_dict()
            )
            self._last_weather_type = state.precipitation_type

        # 3. Synchronize Thermal Environment for Active Citizens
        if hasattr(context, "npcs") and context.npcs:
            for npc in context.npcs.values():
                if not getattr(npc, "is_alive", True):
                    continue
                loc_id = npc.location_id or "room_village_square"
                r_temp = self.climate_engine.get_room_temperature(loc_id, context, tick)
                npc._current_room_temperature = r_temp

                # Somatic freezing penalty if exposed to sub-zero temperatures without bed/fire
                if r_temp < 0.0 and getattr(npc, "current_action", "") not in ("SLEEP_REST", "HEARTH_WARMTH"):
                    npc.adjust_feeling("stress", 0.02)
