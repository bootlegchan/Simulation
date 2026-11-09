"""Live statistical telemetry feeds and real-time engine metric time-series."""
from typing import Any, Dict, List, Optional

class LiveTelemetryEngine:
    """Collects, aggregates, and serves real-time demographic, psychological, economic, and physical metrics."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.max_history_length: int = 1000

    def capture_telemetry(self, engine: Any) -> Dict[str, Any]:
        """Gathers a live diagnostic snapshot from an active simulation engine."""
        from src.economy.macro import MacroEconomicTracker

        alive_npcs = [n for n in engine.npcs.values() if getattr(n, "is_alive", True)]
        total_pop = len(engine.npcs)
        alive_count = len(alive_npcs)
        deceased_count = total_pop - alive_count

        # Psychological averages
        if alive_count > 0:
            avg_contentment = sum(float(n.feelings.get("contentment", 50.0)) for n in alive_npcs) / alive_count
            avg_stress = sum(float(n.feelings.get("stress", 0.0)) for n in alive_npcs) / alive_count
            avg_loneliness = sum(float(n.feelings.get("loneliness", 0.0)) for n in alive_npcs) / alive_count
            avg_pride = sum(float(n.feelings.get("pride", 0.0)) for n in alive_npcs) / alive_count
        else:
            avg_contentment, avg_stress, avg_loneliness, avg_pride = 50.0, 0.0, 0.0, 0.0

        # Economic macro
        treasury_bal = float(getattr(engine.context.municipal_treasury, "balance", 0.0)) if hasattr(engine.context, "municipal_treasury") else 0.0
        total_curr = MacroEconomicTracker.calculate_total_currency(engine.npcs, treasury_bal, context=engine.context)
        gini = MacroEconomicTracker.calculate_gini_coefficient(engine.npcs)

        sc_eng = engine.context.get_service("supply_chain_engine") if hasattr(engine.context, "get_service") else None
        stocks = {k: round(v, 1) for k, v in sc_eng.commodity_stocks.items()} if sc_eng and hasattr(sc_eng, "commodity_stocks") else {}
        prices = {k: round(sc_eng.calculate_market_price(k), 2) for k in sc_eng.commodity_stocks.keys()} if sc_eng and hasattr(sc_eng, "commodity_stocks") else {}

        # Climate
        clim_eng = engine.context.get_service("micro_climate_engine") if hasattr(engine.context, "get_service") else None
        weather = getattr(clim_eng, "current_weather", None) if clim_eng else None
        temp_c = float(weather.ambient_temperature) if weather else 18.0
        weather_cond = weather.precipitation_type.value if weather else "CLEAR"
        season = weather.season if weather else "SPRING"

        # Households
        hh_eng = engine.context.get_service("household_economy_engine") if hasattr(engine.context, "get_service") else None
        households_count = len(hh_eng.households) if hh_eng and hasattr(hh_eng, "households") else 0

        # Volition & Means-End
        vol_eng = engine.context.get_service("means_end_volition_engine") if hasattr(engine.context, "get_service") else None
        vol_telemetry = vol_eng.get_telemetry() if vol_eng and hasattr(vol_eng, "get_telemetry") else {}

        # Skills & Attributes averages
        skills_tracked = ["smithing", "farming", "baking", "crafting", "subterfuge"]
        skills_avg = {}
        for sk in skills_tracked:
            skills_avg[sk] = round(sum(n.get_skill(sk) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 25.0

        phys_avg = {
            "work_rate": round(sum(float(n.physical_attributes.get("work_rate", 55.0)) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 55.0,
            "stamina": round(sum(float(n.physical_attributes.get("stamina", 50.0)) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 50.0
        }
        mental_avg = {
            "leadership": round(sum(float(n.mental_attributes.get("leadership", 40.0)) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 40.0,
            "ambition": round(sum(float(n.mental_attributes.get("ambition", 50.0)) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 50.0,
            "composure": round(sum(float(n.mental_attributes.get("composure", 50.0)) for n in alive_npcs) / max(1, alive_count), 1) if alive_npcs else 50.0
        }

        tick = engine.clock.current_tick if hasattr(engine, "clock") and engine.clock else 0
        time_iso = engine.clock.current_virtual_time_iso if hasattr(engine, "clock") and engine.clock else f"Tick {tick}"

        snapshot = {
            "tick": tick,
            "time_iso": time_iso,
            "demographics": {
                "population": alive_count,
                "total_population": total_pop,
                "alive_count": alive_count,
                "deceased_count": deceased_count,
                "households_count": households_count
            },
            "psychology": {
                "avg_contentment": round(avg_contentment, 2),
                "avg_stress": round(avg_stress, 2),
                "avg_loneliness": round(avg_loneliness, 2),
                "avg_pride": round(avg_pride, 2)
            },
            "economy": {
                "total_currency_gold": round(total_curr, 2),
                "gini_coefficient": round(gini, 3),
                "treasury_balance_gold": round(treasury_bal, 2),
                "commodity_stocks": stocks,
                "commodity_prices": prices
            },
            "urban": {
                "avg_integrity": 100.0,
                "ambient_temperature_celsius": round(temp_c, 1),
                "weather_condition": weather_cond,
                "season": season
            },
            "skills": skills_avg,
            "physical_attributes": phys_avg,
            "mental_attributes": mental_avg,
            "means_end_volition": vol_telemetry
        }
        return snapshot

    def record_tick(self, engine: Any) -> Dict[str, Any]:
        """Captures a snapshot and appends it to rolling diagnostic history."""
        snapshot = self.capture_telemetry(engine)
        self.history.append(snapshot)
        if len(self.history) > self.max_history_length:
            self.history = self.history[-self.max_history_length:]
        return snapshot

    def get_latest(self, engine: Optional[Any] = None) -> Dict[str, Any]:
        """Returns the most recent real telemetry snapshot."""
        if self.history:
            return self.history[-1]
        if engine is not None:
            return self.capture_telemetry(engine)
        return {
            "tick": 0,
            "time_iso": "2026-01-01T00:00:00+00:00",
            "demographics": {"population": 0, "total_population": 0},
            "psychology": {"avg_contentment": 50.0, "avg_stress": 0.0, "avg_loneliness": 0.0},
            "economy": {"total_currency_gold": 0.0, "gini_coefficient": 0.0, "treasury_balance_gold": 0.0},
            "urban": {"avg_integrity": 100.0, "ambient_temperature_celsius": 18.0},
            "skills": {},
            "physical_attributes": {},
            "mental_attributes": {}
        }

    def get_feed(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the latest N diagnostic history frames."""
        return self.history[-limit:]

    def get_metric_timeseries(self, metric: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Extracts a chronological time-series for any metric (e.g. 'avg_contentment',
        'economy.total_currency_gold', 'gini_coefficient', 'demographics.population').
        """
        results: List[Dict[str, Any]] = []
        for s in self.history[-limit:]:
            val = None
            if metric in s:
                val = s[metric]
            elif "." in metric:
                parts = metric.split(".")
                curr = s
                for p in parts:
                    if isinstance(curr, dict) and p in curr:
                        curr = curr[p]
                    else:
                        curr = None
                        break
                val = curr
            else:
                # Search shallow child dictionaries
                for k in ("psychology", "economy", "demographics", "urban", "skills"):
                    if k in s and isinstance(s[k], dict) and metric in s[k]:
                        val = s[k][metric]
                        break

            if val is not None:
                results.append({
                    "tick": s.get("tick", 0),
                    "time_iso": s.get("time_iso", ""),
                    "value": val
                })

        if not results and self.history:
            return [{"tick": s.get("tick", 0), "time_iso": s.get("time_iso", ""), "value": 0.0} for s in self.history[-limit:]]
        return results
