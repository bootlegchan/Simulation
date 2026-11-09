"""Comprehensive End-of-Simulation Dossier Reporter."""
from typing import Any, Dict, List, Optional
from src.economy.macro import MacroEconomicTracker

class DeepSimulationReporter:
    """Compiles end-of-simulation dossiers and comprehensive multi-dimensional analytical reports."""

    def __init__(self):
        self.initial_snapshot_captured: bool = False
        self.initial_pop_count: int = 0
        self.initial_total_currency: float = 0.0
        self.initial_gini: float = 0.0
        self.initial_classes: Dict[str, int] = {}
        self.initial_commodity_stocks: Dict[str, float] = {}
        self.daily_snapshots: List[Dict[str, Any]] = []
        self.decrees_enacted_count: int = 0
        self.infections_by_vector: Dict[str, int] = {"WATER_SICKNESS": 0}
        self.total_fraternal_claims_paid: float = 0.0

    def capture_initial_baseline(self, context: Any, start_tick: int = 0) -> None:
        """Captures ground-truth economic, demographic, and class baseline upon scenario initialization."""
        alive_npcs = [n for n in context.npcs.values() if getattr(n, "is_alive", True)]
        self.initial_pop_count = len(alive_npcs)

        treasury = float(getattr(context.municipal_treasury, "balance", 0.0)) if hasattr(context, "municipal_treasury") else 0.0
        self.initial_total_currency = MacroEconomicTracker.calculate_total_currency(context.npcs, treasury, context=context)
        self.initial_gini = MacroEconomicTracker.calculate_gini_coefficient(context.npcs)

        self.initial_classes = {}
        for n in alive_npcs:
            sp = getattr(n, "social_profile", {}) or {}
            c_type = sp.get("social_class", "COMMONER")
            self.initial_classes[c_type] = self.initial_classes.get(c_type, 0) + 1

        sc = context.get_service("supply_chain_engine") if hasattr(context, "get_service") else None
        if sc and hasattr(sc, "commodity_stocks"):
            self.initial_commodity_stocks = {k: round(v, 1) for k, v in sc.commodity_stocks.items()}

        self.initial_snapshot_captured = True

    def generate_report_data(self, context: Any) -> Dict[str, Any]:
        """Synthesizes comprehensive multi-domain end-of-run simulation dossier."""
        if not self.initial_snapshot_captured:
            self.capture_initial_baseline(context)

        alive_npcs = [n for n in context.npcs.values() if getattr(n, "is_alive", True)]
        deceased_npcs = [n for n in context.npcs.values() if not getattr(n, "is_alive", True)]
        cur_pop = len(alive_npcs)

        # Economic totals
        treasury = float(getattr(context.municipal_treasury, "balance", 0.0)) if hasattr(context, "municipal_treasury") else 0.0
        final_currency = MacroEconomicTracker.calculate_total_currency(context.npcs, treasury, context=context)
        final_gini = MacroEconomicTracker.calculate_gini_coefficient(context.npcs)

        # Psychological distributions
        feelings_stats: Dict[str, Dict[str, float]] = {}
        for f in ("contentment", "stress", "loneliness", "pride", "guilt", "resentment"):
            vals = [float(n.feelings.get(f, 0.0)) for n in alive_npcs]
            if vals:
                feelings_stats[f] = {
                    "mean": round(sum(vals) / len(vals), 2),
                    "min": round(min(vals), 2),
                    "max": round(max(vals), 2)
                }
            else:
                feelings_stats[f] = {"mean": 50.0, "min": 50.0, "max": 50.0}

        # Supply chain stocks
        sc = context.get_service("supply_chain_engine") if hasattr(context, "get_service") else None
        stocks = {k: round(v, 1) for k, v in sc.commodity_stocks.items()} if sc and hasattr(sc, "commodity_stocks") else {}
        prices = {k: round(sc.calculate_market_price(k), 2) for k in sc.commodity_stocks.keys()} if sc and hasattr(sc, "commodity_stocks") else {}

        # Demise statistics
        demise_eng = context.get_service("demise_engine") if hasattr(context, "get_service") else None
        deaths_count = getattr(demise_eng, "total_deaths_count", len(deceased_npcs)) if demise_eng else len(deceased_npcs)

        # Justice & Governance
        court_eng = context.get_service("courtroom_lawsuit_engine") if hasattr(context, "get_service") else None
        lawsuits_active = len(court_eng.active_lawsuits) if court_eng and hasattr(court_eng, "active_lawsuits") else 0
        lawsuits_resolved = len(court_eng.lawsuit_history) if court_eng and hasattr(court_eng, "lawsuit_history") else 0

        decree_eng = context.get_service("municipal_decree_engine") if hasattr(context, "get_service") else None
        active_decrees = [d.title for d in decree_eng.active_decrees.values()] if decree_eng and hasattr(decree_eng, "active_decrees") else []

        # Epistemic system
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
        atoms_count = len(ep_eng.atoms) if ep_eng and hasattr(ep_eng, "atoms") else 0
        board_posts = getattr(ep_eng, "total_notice_board_posts", 0) if ep_eng else 0
        board_reads = getattr(ep_eng, "total_notice_board_reads", 0) if ep_eng else 0

        # Means-end volition
        vol_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
        vol_data = vol_eng.get_telemetry() if vol_eng and hasattr(vol_eng, "get_telemetry") else {}

        # Career totals & competencies
        skills_tracked = ["smithing", "farming", "baking", "crafting", "subterfuge", "hospitality"]
        radar = {sk: round(sum(n.get_skill(sk) for n in alive_npcs) / max(1, cur_pop), 1) for sk in skills_tracked} if alive_npcs else {}

        cur_tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {cur_tick}"

        total_earnings = sum(
            float(getattr(n, "career_statistics", {}).get("career_earnings_gold", 0.0))
            for n in context.npcs.values()
        )

        return {
            "meta": {
                "current_tick": cur_tick,
                "current_virtual_time": time_iso,
                "total_simulated_days": cur_tick // 1440
            },
            "demographics": {
                "initial_population": self.initial_pop_count,
                "current_alive_population": cur_pop,
                "deceased_population": len(deceased_npcs),
                "social_classes": self.initial_classes
            },
            "psychology": {
                "feelings_summary": feelings_stats
            },
            "economy": {
                "initial_total_currency_gold": round(self.initial_total_currency, 2),
                "final_total_currency_gold": round(final_currency, 2),
                "currency_delta_gold": round(final_currency - self.initial_total_currency, 2),
                "initial_gini": round(self.initial_gini, 3),
                "final_gini": round(final_gini, 3),
                "treasury_balance_gold": round(treasury, 2),
                "commodity_stock_levels": stocks,
                "commodity_market_prices": prices
            },
            "urban": {
                "settlements_count": len(getattr(context, "settlements", {})),
                "total_rooms": sum(len(b.rooms) for s in getattr(context, "settlements", {}).values() for b in s.buildings.values())
            },
            "public_health": {
                "total_deaths": deaths_count,
                "infections_by_vector": self.infections_by_vector
            },
            "governance_and_justice": {
                "active_lawsuits_count": lawsuits_active,
                "resolved_lawsuits_count": lawsuits_resolved,
                "active_decrees": active_decrees
            },
            "information_and_kinship": {
                "epistemic_atoms_created": atoms_count,
                "notice_board_posts": board_posts,
                "notice_board_reads": board_reads
            },
            "agent_competencies": {
                "skills_radar": radar,
                "physical_attributes": {"work_rate_avg": round(sum(float(n.physical_attributes.get("work_rate", 55.0)) for n in alive_npcs) / max(1, cur_pop), 1) if alive_npcs else 55.0},
                "career_totals": {"total_earnings_sum": round(total_earnings, 1)}
            },
            "facility_profiles": {
                "total_repair_deficit_gold": 0.0
            },
            "means_end_volition": vol_data
        }
