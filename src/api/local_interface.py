"""Simulation Connector and Visual API."""
from typing import Any, Dict, List

class SimulationConnector:
    def __init__(self, engine: Any):
        self.engine = engine

    def get_commodity_stocks(self) -> Dict[str, int]:
        return {"food_bread": 30, "raw_wheat": 20, "flour": 15}

    def get_faction_statuses(self) -> Dict[str, Any]:
        return {}

    def get_active_grudges(self) -> List[Any]:
        return []

    def get_mentorship_history(self) -> List[Any]:
        return []

    def get_pending_lawsuits(self) -> List[Any]:
        court = self.engine.context.get_service("courtroom_lawsuit_engine")
        return list(court.active_lawsuits.values()) if court else []

    def get_active_domestic_spats(self) -> List[Any]:
        return []

    def get_power_contracts(self) -> List[Any]:
        return []

class LocalVisualAPI:
    def __init__(self, engine: Any):
        self.engine = engine
