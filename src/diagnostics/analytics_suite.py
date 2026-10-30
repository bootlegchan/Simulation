import json
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from src.simulation.engine import SimulationEngine
from src.diagnostics.professional_auditor import ProfessionalAuditor
from src.economy.macro import MacroEconomicTracker
from src.society.vices_and_crime import ViceTracker, DarkCrimeEngine

class CustomScenarioInjector:
    """Framework for injecting custom events and asserting context-aware outcomes."""

    def __init__(self, name: str):
        self.name = name
        self.injection_ticks: Dict[int, Callable[[SimulationEngine], None]] = {}
        self.assertion_ticks: Dict[int, Callable[[SimulationEngine], Dict[str, Any]]] = {}

    def add_injection(self, tick: int, action: Callable[[SimulationEngine], None]) -> None:
        self.injection_ticks[tick] = action

    def add_assertion(self, tick: int, assertion: Callable[[SimulationEngine], Dict[str, Any]]) -> None:
        self.assertion_ticks[tick] = assertion

class ModularAnalyticsSuite:
    """Unified Diagnostic Analysis Suite allowing preset test suites and custom scenario injectors."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def run_preset_suite(self, suite_name: str, seed: int = 42, ticks: int = 1440) -> Dict[str, Any]:
        """Runs one of the preset diagnostic suites."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=seed)
        engine.start()

        if suite_name == "longitudinal_macro":
            engine.tick(ticks)
            gini = MacroEconomicTracker.calculate_gini_coefficient(engine.npcs)
            total_wealth = MacroEconomicTracker.calculate_total_currency(engine.npcs)
            return {
                "suite": suite_name,
                "ticks_run": ticks,
                "gini_coefficient": round(gini, 3),
                "total_wealth_gold": round(total_wealth, 2),
                "npc_count": len(engine.npcs)
            }
        elif suite_name == "crime_and_vices":
            # Simulate 1 day with vice tracking
            auditor = ProfessionalAuditor(engine)
            engine.tick( ticks )
            auditor.audit_tick()
            
            vice_count = sum(1 for npc in engine.npcs.values() if any(v > 20.0 for v in npc.vices.values()))
            return {
                "suite": suite_name,
                "ticks_run": ticks,
                "npcs_with_vices": vice_count,
                "audited_records": len(auditor.records)
            }
        else:
            engine.tick(ticks)
            return {"suite": suite_name, "status": "completed", "ticks_run": ticks}

    def run_custom_scenario(self, injector: CustomScenarioInjector, seed: int = 42, total_ticks: int = 1440) -> Dict[str, Any]:
        """Executes a custom scenario injector over total_ticks."""
        engine = SimulationEngine(self.data_dir)
        engine.initialize(seed=seed)
        engine.start()

        assertion_results = []

        for t in range(1, total_ticks + 1):
            engine.tick(1)
            current_tick = engine.clock.current_tick

            if current_tick in injector.injection_ticks:
                injector.injection_ticks[current_tick](engine)

            if current_tick in injector.assertion_ticks:
                res = injector.assertion_ticks[current_tick](engine)
                assertion_results.append({"tick": current_tick, "result": res})

        return {
            "scenario_name": injector.name,
            "total_ticks": total_ticks,
            "assertion_results": assertion_results,
            "final_virtual_time": engine.clock.current_virtual_time_iso
        }
