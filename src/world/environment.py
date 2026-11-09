"""Environmental states, seasons, weather, and utility modifiers."""
from enum import Enum
from typing import Dict

class WeatherType(Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    SNOW = "SNOW"

class TimeOfDay(Enum):
    DAWN = "DAWN"
    DAY = "DAY"
    DUSK = "DUSK"
    NIGHT = "NIGHT"

class EnvironmentState:
    def __init__(self, weather: WeatherType = WeatherType.CLEAR, season: str = "SUMMER"):
        self.weather = weather
        self.season = season

    def calculate_utility_modifiers(self, hour: int) -> Dict[str, float]:
        mods: Dict[str, float] = {}
        if hour >= 22 or hour < 6:
            mods["rest"] = 40.0
            mods["work_production"] = -30.0
        elif 8 <= hour < 18:
            mods["work_production"] = 25.0
            mods["rest"] = -20.0
        return mods
