class DynamicPricingEngine:
    """Dynamic pricing based on supply/demand ratio and item quality."""

    @staticmethod
    def calculate_price(base_value: float, supply: int, demand: int, quality: float = 1.0) -> float:
        supply = max(0, supply)
        demand = max(1, demand)
        demand_ratio = float(demand - supply) / float(supply + 1.0)
        scarcity_multiplier = max(0.5, min(3.0, 1.0 + demand_ratio))
        quality_multiplier = max(0.5, min(2.5, 0.8 + 0.2 * quality))
        return round(base_value * scarcity_multiplier * quality_multiplier, 2)
