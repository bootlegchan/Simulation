"""
Continuous Weather, Micro-Climate, and Room Thermodynamics Engine.
Operates on continuous solar diurnal curves, barometric pressure drift,
dynamic room thermodynamics (insulation, hearth combustion, body heat),
and somatic thermal comfort without implicit state machines.
Enhanced with seed-driven seasonal starting dates and atmospheric phase variation.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

class WeatherType(str, Enum):
    CLEAR = "CLEAR"
    CLOUDY = "CLOUDY"
    OVERCAST = "OVERCAST"
    RAIN = "RAIN"
    SLEET = "SLEET"
    SNOW = "SNOW"
    BLIZZARD = "BLIZZARD"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

@dataclass
class ContinuousWeatherState:
    tick: int
    season: str
    hour: float
    day_of_year: int
    ambient_temperature: float          # Outdoor temperature in °C
    diurnal_temperature_offset: float   # Sinusoidal solar heating offset in °C
    barometric_pressure_kpa: float      # Atmospheric pressure (baseline ~101.32 kPa)
    precipitation_intensity: float      # 0.0 (bone dry) to 1.0 (torrential / heavy blizzard)
    precipitation_type: WeatherType     # CLEAR, CLOUDY, OVERCAST, RAIN, SLEET, SNOW, BLIZZARD
    cloud_cover: float                  # 0.0 to 1.0
    humidity: float                     # 0.0 to 1.0
    wind_speed_kmh: float               # Wind velocity in km/h
    solar_intensity: float              # Direct solar radiation (0.0 at night, up to 1.0 at solar noon)
    is_stormy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "season": self.season,
            "hour": round(self.hour, 2),
            "day_of_year": self.day_of_year,
            "ambient_temperature": round(self.ambient_temperature, 2),
            "diurnal_temperature_offset": round(self.diurnal_temperature_offset, 2),
            "barometric_pressure_kpa": round(self.barometric_pressure_kpa, 2),
            "precipitation_intensity": round(self.precipitation_intensity, 3),
            "precipitation_type": self.precipitation_type.value if hasattr(self.precipitation_type, "value") else str(self.precipitation_type),
            "cloud_cover": round(self.cloud_cover, 2),
            "humidity": round(self.humidity, 2),
            "wind_speed_kmh": round(self.wind_speed_kmh, 1),
            "solar_intensity": round(self.solar_intensity, 2),
            "is_stormy": self.is_stormy
        }

class MicroClimateEngine:
    """
    Thermodynamic and Meteorological Engine.
    Simulates continuous outdoor weather and indoor room thermodynamics
    driven 100% by data/settings/weather_and_climate.json.
    """
    _instance: Optional["MicroClimateEngine"] = None

    @classmethod
    def get_instance(cls) -> "MicroClimateEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.current_weather: Optional[ContinuousWeatherState] = None
        self.room_temperatures: Dict[str, float] = {}
        self.weather_history: List[ContinuousWeatherState] = []
        self.hearth_fuel_levels: Dict[str, float] = {}
        self.start_day_offset: int = 0
        self.seed_phase: float = 0.0

    def apply_seed_initialization(self, seed: int = 42) -> None:
        """Initializes starting seasonal offset and barometric phase dynamically from simulation seed."""
        cfg = self.get_climate_config()
        init_cfg = cfg.get("seasonal_initialization", {})
        default_season = init_cfg.get("default_season", "RANDOM_BY_SEED")
        offsets = init_cfg.get("season_offsets", {"WINTER": 0, "SPRING": 90, "SUMMER": 180, "AUTUMN": 270})

        if default_season == "RANDOM_BY_SEED":
            # Select season pseudo-randomly via seed
            season_choices = ["WINTER", "SPRING", "SUMMER", "AUTUMN"]
            chosen = season_choices[seed % len(season_choices)]
            self.start_day_offset = offsets.get(chosen, 0)
        else:
            self.start_day_offset = offsets.get(default_season, 0)

        self.seed_phase = float((seed * 137.5) % 1000.0)

    def get_climate_config(self) -> Dict[str, Any]:
        settings = SettingsRegistry.get_instance().get("weather_and_climate")
        return settings.get("climate_system", self.config)

    def determine_season(self, day_of_year: int) -> str:
        """Calculates seasonal quarter continuously from day of year (0 to 359)."""
        effective_day = (day_of_year + self.start_day_offset) % 360
        if 0 <= effective_day < 90:
            return "WINTER"
        elif 90 <= effective_day < 180:
            return "SPRING"
        elif 180 <= effective_day < 270:
            return "SUMMER"
        else:
            return "AUTUMN"

    def update_weather(self, tick: int, context: Optional[Any] = None) -> ContinuousWeatherState:
        """
        Calculates the continuous meteorological field at virtual tick.
        Uses sinusoidal diurnal curves, seasonal baselines, and continuous barometric pressure drift.
        """
        cfg = self.get_climate_config()
        seasons_cfg = cfg.get("seasons", {})
        baro_cfg = cfg.get("barometric_dynamics", {})

        if context and hasattr(context, "clock") and hasattr(context.clock, "current_virtual_time"):
            vt = context.clock.current_virtual_time
            hour = vt.hour + (vt.minute / 60.0)
        else:
            hour = (6.0 + (tick / 60.0)) % 24.0

        day_of_year = (tick // 1440) % 360
        season = self.determine_season(day_of_year)
        s_spec = seasons_cfg.get(season, seasons_cfg.get("SUMMER", {}))

        mean_temp = float(s_spec.get("mean_temp", 15.0))
        diurnal_amp = float(s_spec.get("diurnal_amplitude", 6.0))
        solar_peak = float(s_spec.get("solar_peak_hour", 13.0))
        snow_thresh = float(s_spec.get("snow_threshold_temp", 0.0))
        base_humid = float(s_spec.get("base_humidity", 0.60))

        # 1. Continuous Diurnal Solar Curve
        # Peak solar heating at solar_peak (13:00); coldest at 01:00
        solar_angle = 2.0 * math.pi * (hour - (solar_peak - 6.0)) / 24.0
        diurnal_offset = diurnal_amp * math.sin(solar_angle)

        # 2. Continuous Barometric Pressure Drift (harmonic drift with seed phase shift)
        p_base = float(baro_cfg.get("baseline_pressure_kpa", 101.32))
        p_drift = (
            1.25 * math.sin((tick + self.seed_phase) / 1800.0) +
            0.85 * math.cos((tick + self.seed_phase) / 4320.0) +
            0.45 * math.sin((tick + self.seed_phase * 1.5) / 720.0)
        )
        baro_pressure = p_base + p_drift

        # Cloud cover and precipitation derived continuously from pressure
        cloud_cover = max(0.0, min(1.0, (102.20 - baro_pressure) / 2.0))
        p_thresh = float(baro_cfg.get("precipitation_low_pressure_threshold_kpa", 100.80))
        
        if baro_pressure < p_thresh:
            precip_intensity = min(1.0, (p_thresh - baro_pressure) / 1.1)
        else:
            precip_intensity = 0.0

        # Ambient Outdoor Temperature
        ambient_temp = mean_temp + diurnal_offset + ((baro_pressure - p_base) * 0.75) - (precip_intensity * 2.2)

        # Precipitation Type
        if precip_intensity <= 0.04:
            if cloud_cover < 0.35:
                precip_type = WeatherType.CLEAR
            elif cloud_cover < 0.75:
                precip_type = WeatherType.CLOUDY
            else:
                precip_type = WeatherType.OVERCAST
        else:
            if ambient_temp <= snow_thresh:
                precip_type = WeatherType.BLIZZARD if precip_intensity > 0.70 else WeatherType.SNOW
            elif ambient_temp <= (snow_thresh + 1.8):
                precip_type = WeatherType.SLEET
            else:
                precip_type = WeatherType.RAIN

        wind_speed = 8.0 + (18.0 * (1.0 - cloud_cover * 0.5)) + (precip_intensity * 22.0)
        humidity = max(0.20, min(0.98, base_humid + (precip_intensity * 0.35) - (diurnal_offset * 0.02)))
        solar_intensity = max(0.0, math.sin(solar_angle)) * (1.0 - (cloud_cover * 0.75)) if (6.0 <= hour <= 20.0) else 0.0
        is_stormy = precip_intensity >= 0.60 or precip_type in (WeatherType.BLIZZARD,)

        state = ContinuousWeatherState(
            tick=tick,
            season=season,
            hour=hour,
            day_of_year=(day_of_year + self.start_day_offset) % 360,
            ambient_temperature=ambient_temp,
            diurnal_temperature_offset=diurnal_offset,
            barometric_pressure_kpa=baro_pressure,
            precipitation_intensity=precip_intensity,
            precipitation_type=precip_type,
            cloud_cover=cloud_cover,
            humidity=humidity,
            wind_speed_kmh=wind_speed,
            solar_intensity=solar_intensity,
            is_stormy=is_stormy
        )
        self.current_weather = state
        return state

    def get_room_temperature(
        self,
        room_id: str,
        context: Optional[Any] = None,
        tick: Optional[int] = None
    ) -> float:
        """
        Computes the continuous thermodynamic temperature of a room (°C).
        Accounts for building insulation, active hearth/oven combustion,
        human occupant body heat, and thermal inertia.
        """
        if not room_id:
            return self.current_weather.ambient_temperature if self.current_weather else 18.0

        cfg = self.get_climate_config()
        thermo_cfg = cfg.get("thermodynamics", {})
        insul_map = thermo_cfg.get("building_insulation_retention", {})
        hearth_heat = float(thermo_cfg.get("hearth_heat_output_celsius", 18.0))
        body_heat_rate = float(thermo_cfg.get("occupant_body_heat_celsius", 0.35))
        alpha = float(thermo_cfg.get("thermal_inertia_alpha", 0.15))

        ambient = self.current_weather.ambient_temperature if self.current_weather else 18.0

        # Check if room is an outdoor space
        r_low = room_id.lower()
        is_outdoor = any(k in r_low for k in ("square", "plaza", "quay", "street", "road", "field", "garden", "market"))
        if is_outdoor:
            self.room_temperatures[room_id] = round(ambient, 2)
            return round(ambient, 2)

        # Indoor Thermodynamics
        bldg_cat = "RESIDENTIAL"
        has_hearth = any(k in r_low for k in ("hearth", "oven", "forge", "kitchen", "tavern", "bakery", "blacksmith"))
        occupants_count = 0

        if context:
            if hasattr(context, "find_building_by_room_id"):
                bldg = context.find_building_by_room_id(room_id)
                if bldg and hasattr(bldg, "category"):
                    bldg_cat = getattr(bldg, "category", "RESIDENTIAL").upper()

            if hasattr(context, "find_room_by_id"):
                r_obj = context.find_room_by_id(room_id)
                if r_obj:
                    for oid in getattr(r_obj, "contained_object_ids", []):
                        obj = context.objects.get(oid) if hasattr(context, "objects") else None
                        if obj and (obj.has_capability("family_gathering") or any(k in obj.name.lower() for k in ("hearth", "stove", "oven", "forge"))):
                            has_hearth = True
                            break

            if hasattr(context, "npcs"):
                occupants_count = sum(1 for n in context.npcs.values() if n.location_id == room_id and getattr(n, "is_alive", True))

        insulation = float(insul_map.get(bldg_cat, insul_map.get("DEFAULT", 0.70)))
        base_equilibrium = ambient + max(0.0, (20.0 - ambient) * insulation)

        if has_hearth:
            base_equilibrium += hearth_heat

        base_equilibrium += (occupants_count * body_heat_rate)

        prev_temp = self.room_temperatures.get(room_id, base_equilibrium)
        new_temp = prev_temp + alpha * (base_equilibrium - prev_temp)
        self.room_temperatures[room_id] = round(new_temp, 2)
        return self.room_temperatures[room_id]

    def calculate_ambient_temperature(self, season: str = "WINTER", time_of_day: str = "NIGHT") -> float:
        cfg = self.get_climate_config()
        seasons_cfg = cfg.get("seasons", {})
        s_spec = seasons_cfg.get(season.upper(), {})
        mean_temp = float(s_spec.get("mean_temp", -3.5 if season.upper() == "WINTER" else 18.0))
        diurnal_amp = float(s_spec.get("diurnal_amplitude", 4.0 if season.upper() == "WINTER" else 6.0))
        offset = -diurnal_amp if time_of_day.upper() == "NIGHT" else diurnal_amp
        return round(mean_temp + offset, 1)

    def calculate_indoor_room_temperature(
        self,
        room: Any,
        building: Any,
        season: str = "WINTER",
        hour: int = 12,
        objects_dict: Optional[Dict[str, Any]] = None
    ) -> float:
        is_night = (hour >= 22 or hour < 6)
        ambient = self.calculate_ambient_temperature(season, "NIGHT" if is_night else "DAY")

        r_id = getattr(room, "id", "") if room else ""
        r_name = (getattr(room, "name", "") or r_id).lower()

        has_hearth = "hearth" in r_name or "oven" in r_name
        if objects_dict and room:
            for oid in getattr(room, "contained_object_ids", []):
                obj = objects_dict.get(oid)
                if obj and (obj.has_capability("family_gathering") or "hearth" in getattr(obj, "name", "").lower()):
                    has_hearth = True
                    break

        bldg_cat = getattr(building, "category", "RESIDENTIAL").upper() if building else "RESIDENTIAL"
        insulation_offset = 12.0
        hearth_offset = 16.0 if has_hearth else 0.0

        return round(ambient + insulation_offset + hearth_offset, 1)

WeatherAndClimateEngine = MicroClimateEngine
