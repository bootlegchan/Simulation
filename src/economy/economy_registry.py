"""Dynamic Economy Registry."""
from typing import Any, Dict, Optional

class DynamicEconomyRegistry:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.prices = {"bread_loaf": 3.0, "food_bread": 3.0, "raw_wheat": 1.5, "flour": 2.0}

    def get_commodity_price(self, commodity_id: str) -> float:
        return self.prices.get(commodity_id, 3.0)

    def get_commercial_sales_tax_rate(self) -> float:
        return 0.05
