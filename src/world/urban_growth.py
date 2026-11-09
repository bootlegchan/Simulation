"""Urban Growth and Infrastructure Maintenance with Municipal Reserve Brake."""
from typing import Any, Dict

class UrbanGrowthEngine:
    def __init__(self):
        pass

    def process_daily_lifecycle(self, settlement: Any, npcs: Dict[str, Any], municipal_treasury: Any, current_tick: int, economic_multiplier: float = 1.0, context: Any = None) -> Dict[str, Any]:
        from src.configuration.settings import SettingsRegistry
        gov_cfg = SettingsRegistry.get_instance().get("civic_governance")
        treasury_cfg = gov_cfg.get("treasury", {})
        reserve_brake = float(treasury_cfg.get("reserve_brake_gold", 150.0))
        daily_cap = float(treasury_cfg.get("daily_maintenance_cap_gold", 15.0))
        poverty_ceiling = float(treasury_cfg.get("indigent_relief_wealth_ceiling_gold", 15.0))
        max_recipients = int(treasury_cfg.get("max_relief_recipients", 3))

        if municipal_treasury and hasattr(municipal_treasury, "balance") and municipal_treasury.balance >= reserve_brake:
            spend = min(daily_cap, municipal_treasury.balance - reserve_brake)
            if spend > 0:
                municipal_treasury.balance = round(municipal_treasury.balance - spend, 2)
                laborers = [n for n in npcs.values() if getattr(n, "is_alive", True) and n.wealth < poverty_ceiling]
                if laborers:
                    recipients = laborers[:max_recipients]
                    payout = round(spend / len(recipients), 2)
                    for l in recipients:
                        l.wealth = round(l.wealth + payout, 2)
                        l.record_stat("career_earnings_gold", payout)
        return {"maintained": True, "tick": current_tick}
