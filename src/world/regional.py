"""
Inter-Settlement Trade Caravans, Regional Economics, and Climate Shocks.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.item import ItemInstance

@dataclass
class MerchantCaravan:
    caravan_id: str
    origin_settlement_id: str
    destination_settlement_id: str
    cargo: List[ItemInstance] = field(default_factory=list)
    travel_progress: float = 0.0  # 0.0 to 100.0%
    speed: float = 5.0
    status: str = "TRAVELING"  # "TRAVELING", "ARRIVED", "RAIDED"

class RegionalTradeManager:
    """Manages trade routes and traveling merchant caravans across settlements."""

    def __init__(self):
        self.caravans: Dict[str, MerchantCaravan] = {}
        self.regional_settlements: Dict[str, Dict[str, Any]] = {
            "settlement_pineridge": {"name": "Pine Ridge", "distance_miles": 12.0, "demand": "food_bread"},
            "settlement_riverdale": {"name": "Riverdale", "distance_miles": 25.0, "demand": "tools_hammer"},
        }

    def dispatch_caravan(
        self,
        caravan_id: str,
        origin_id: str,
        dest_id: str,
        cargo_items: List[ItemInstance]
    ) -> MerchantCaravan:
        caravan = MerchantCaravan(
            caravan_id=caravan_id,
            origin_settlement_id=origin_id,
            destination_settlement_id=dest_id,
            cargo=list(cargo_items),
        )
        self.caravans[caravan_id] = caravan
        return caravan

    def advance_caravans(self, bandit_risk: float = 0.05) -> List[Dict[str, Any]]:
        events = []
        for c_id, caravan in list(self.caravans.items()):
            if caravan.status == "TRAVELING":
                caravan.travel_progress += caravan.speed
                if caravan.travel_progress >= 100.0:
                    caravan.status = "ARRIVED"
                    events.append({"caravan_id": c_id, "event_type": "caravan_arrived", "destination": caravan.destination_settlement_id})
                elif bandit_risk > 0.15 and caravan.travel_progress > 50.0 and caravan.status != "RAIDED":
                    caravan.status = "RAIDED"
                    caravan.cargo.clear()
                    events.append({"caravan_id": c_id, "event_type": "caravan_raided", "location": "Trade Route Road"})

        return events

class RegionalClimateManager:
    """Manages regional seasons and climate shocks affecting crop growth and spoilage."""

    SEASONS = ["SPRING", "SUMMER", "AUTUMN", "WINTER"]

    def __init__(self, current_season: str = "SPRING"):
        self.current_season = current_season if current_season in self.SEASONS else "SPRING"
        self.active_shock: Optional[str] = None  # None, "DROUGHT", "FROST", "BANDIT_RAID", "HARVEST_BOOM"

    def advance_season(self) -> str:
        curr_idx = self.SEASONS.index(self.current_season)
        self.current_season = self.SEASONS[(curr_idx + 1) % len(self.SEASONS)]
        return self.current_season

    def trigger_shock(self, shock_type: str) -> Dict[str, Any]:
        self.active_shock = shock_type
        crop_modifier = 1.0
        spoilage_modifier = 1.0
        bandit_risk = 0.05

        if shock_type == "DROUGHT":
            crop_modifier = 0.2
        elif shock_type == "FROST":
            crop_modifier = 0.1
            spoilage_modifier = 0.5  # Cold preserves food
        elif shock_type == "BANDIT_RAID":
            bandit_risk = 0.35
        elif shock_type == "HARVEST_BOOM":
            crop_modifier = 2.5

        return {
            "shock_type": shock_type,
            "crop_growth_modifier": crop_modifier,
            "spoilage_modifier": spoilage_modifier,
            "bandit_risk": bandit_risk,
        }

    def clear_shock(self) -> None:
        self.active_shock = None
