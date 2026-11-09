#!/usr/bin/env python3
import sys
from pathlib import Path

base_dir = Path("/workspace/scratch/sim_backend")
sys.path.insert(0, str(base_dir))

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.macro import MacroEconomicTracker

def run_seed(seed: int, days: int = 30):
    ticks = days * 1440
    data_dir = get_default_data_dir()
    engine = SimulationEngine(data_dir)
    engine.initialize(seed=seed)

    init_money = MacroEconomicTracker.calculate_total_currency(
        engine.npcs, getattr(engine.context.municipal_treasury, "balance", 0.0), context=engine.context
    )

    engine.fast_forward(ticks, max_leap=60)

    final_money = MacroEconomicTracker.calculate_total_currency(
        engine.npcs, getattr(engine.context.municipal_treasury, "balance", 0.0), context=engine.context
    )
    gini = MacroEconomicTracker.calculate_gini_coefficient(engine.npcs)
    treasury = getattr(engine.context.municipal_treasury, "balance", 0.0)

    clim = engine.context.get_service("micro_climate_engine")
    weather = clim.current_weather

    sc = engine.context.get_service("supply_chain_engine")
    rom = engine.context.get_service("romance_engine")
    dem = engine.context.get_service("demise_engine")
    jp = engine.context.get_service("job_posting_engine")

    alive_count = sum(1 for n in engine.npcs.values() if n.is_alive)

    print(f"=== SEED {seed} ({days} DAYS / {ticks:,} TICKS) ===")
    print(f"  Population Alive: {alive_count}/48 (Deaths: {dem.total_deaths_count})")
    print(f"  Starting Currency: {init_money:.1f}g -> Final Currency: {final_money:.1f}g (Net: {final_money - init_money:+.1f}g)")
    print(f"  Treasury: {treasury:.2f}g | Gini: {gini:.3f}")
    print(f"  Starting Season: {clim.determine_season(0)} -> Final Weather: {weather.season} {weather.ambient_temperature:.1f}C ({weather.precipitation_type.value})")
    print(f"  Stocks: Wheat: {sc.get_stock_level('raw_wheat'):.1f} | Flour: {sc.get_stock_level('flour'):.1f} | Bread: {sc.get_stock_level('food_bread'):.1f} | Timber: {sc.get_stock_level('raw_timber'):.1f} | Firewood: {sc.get_stock_level('firewood'):.1f}")
    print(f"  Romance: Intimacy Acts: {rom.total_intimacy_acts} | Rejections: {rom.total_intimacy_rejections}")
    print(f"  Jobs Completed: Official: {jp.total_official_jobs_completed} | Illicit: {jp.total_illicit_jobs_completed}")

if __name__ == "__main__":
    for s in [42, 1337, 777]:
        run_seed(s, days=30)
