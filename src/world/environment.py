from enum import Enum
from typing import Dict, Any

class WeatherType(Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    HEAVY_STORM = "HEAVY_STORM"
    COLD_SNAP = "COLD_SNAP"
    HEATWAVE = "HEATWAVE"

class TimeOfDay(Enum):
    DAWN = "DAWN"      # 06:00 - 09:00
    MIDDAY = "MIDDAY"  # 09:00 - 17:00
    DUSK = "DUSK"      # 17:00 - 21:00
    NIGHT = "NIGHT"    # 21:00 - 06:00

class EnvironmentState:
    """Manages dynamic weather, time of day, and environmental utility modifiers."""

    def __init__(self, weather: WeatherType = WeatherType.CLEAR, season: str = "SUMMER"):
        self.weather = weather
        self.season = season

    def get_time_of_day(self, hour: int) -> TimeOfDay:
        if 6 <= hour < 9:
            return TimeOfDay.DAWN
        elif 9 <= hour < 17:
            return TimeOfDay.MIDDAY
        elif 17 <= hour < 21:
            return TimeOfDay.DUSK
        else:
            return TimeOfDay.NIGHT

    def calculate_utility_modifiers(self, hour: int) -> Dict[str, float]:
        tod = self.get_time_of_day(hour)
        mods: Dict[str, float] = {
            "work_production": 0.0,
            "rest": 0.0,
            "socialize": 0.0,
            "vice_indulgence": 0.0,
            "spiritual_devotion": 0.0,
            "crime_illicit": 0.0
        }

        # Time of day effects
        if tod == TimeOfDay.NIGHT:
            mods["rest"] += 50.0
            mods["vice_indulgence"] += 30.0
            mods["crime_illicit"] += 40.0
            mods["work_production"] -= 30.0
        elif tod == TimeOfDay.DUSK:
            mods["socialize"] += 35.0
            mods["vice_indulgence"] += 20.0

        # Weather effects
        if self.weather == WeatherType.HEAVY_STORM:
            mods["work_production"] -= 50.0  # Outdoor work discouraged
            mods["rest"] += 35.0             # Prefer indoor shelter/fireplaces
            mods["socialize"] += 25.0         # Seek tavern/inn shelter
            mods["vice_indulgence"] += 25.0
        elif self.weather == WeatherType.RAIN:
            mods["work_production"] -= 20.0
            mods["rest"] += 15.0
        elif self.weather == WeatherType.COLD_SNAP:
            mods["rest"] += 40.0             # Seek hearth/bed warmth
            mods["spiritual_devotion"] += 20.0

        return mods
