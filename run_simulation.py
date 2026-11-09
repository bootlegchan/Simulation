#!/usr/bin/env python3
"""
Social Simulation Runner (v168).
Elastic Maslow Desire Hierarchy, Flexible Cohabitation Models, and Dwelling Affordance Anchoring.
Executes social simulations with full telemetry, intelligent food selection,
proportional income taxation, indigent legal aid, circadian rhythm dynamics,
Hierarchical Asynchronous Event-Scheduled Time (HAEST), and continuous thermodynamics.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.economy.macro import MacroEconomicTracker
from src.diagnostics.verisimilitude_benchmark import BiographicalDiaryCompiler, VerisimilitudeBenchmarkEngine

def run(days: int = 30, scenario: str = "oakwood_baseline.json", seed: int = 42, stochastic: bool = False, adaptive: bool = False, output_file: Optional[str] = None):
    ticks = days * 1440
    data_dir = get_default_data_dir()
    engine = SimulationEngine(data_dir)
    engine.initialize(seed=seed, scenario_filename=scenario, stochastic=stochastic)

    mode_str = 'STOCHASTIC' if stochastic else f'SEED {seed}'
    print("=" * 80)
    print(f" SOCIAL SIMULATION RUNNER (v168)")
    print(f" Scenario: {scenario} | Mode: {mode_str} | Days: {days} ({ticks:,} ticks)")
    print(f" Engine Time Model: {'HAEST Adaptive Leaping' if adaptive else 'Standard Discrete Step'}")
    print(f" Population: {len(engine.npcs)} | Settlements: {len(engine.settlements)}")
    print("=" * 80)

    t0 = time.time()
    if adaptive:
        engine.fast_forward(ticks, max_leap=60)
    else:
        engine.tick(ticks)
    wall_sec = round(time.time() - t0, 2)

    total_curr = MacroEconomicTracker.calculate_total_currency(engine.npcs, getattr(engine.context.municipal_treasury, "balance", 0.0), context=engine.context)
    gini = MacroEconomicTracker.calculate_gini_coefficient(engine.npcs)

    ep_eng = engine.context.get_service("epistemic_engine")
    club_eng = engine.context.get_service("social_club_engine")
    game_eng = engine.context.get_service("recreation_game_engine")
    mind_eng = engine.context.get_service("attentional_mindspace_engine")
    desire_eng = engine.context.get_service("desire_hierarchy_engine")
    hh_eng = engine.context.get_service("household_economy_engine")

    print(f"Completed in {wall_sec}s ({round(ticks / max(0.01, wall_sec), 1)} ticks/sec)!")
    print(f"Final Currency: {total_curr:.2f}g | Gini: {gini:.3f} | Treasury: {getattr(engine.context.municipal_treasury, 'balance', 0.0):.2f}g")
    if hh_eng:
        types_count = {}
        for h in hh_eng.households.values():
            types_count[h.household_type.value] = types_count.get(h.household_type.value, 0) + 1
        print(f"Cohabitation Households: {len(hh_eng.households)} | Types: {types_count}")
    if desire_eng:
        print(f"Desire Hierarchy Evaluations: {desire_eng.total_evaluations_count:,}")
    if mind_eng:
        print(f"Attentional Mindspace Evaluations: {mind_eng.total_evaluations_count:,} | Spotlight Transitions: {mind_eng.total_spotlight_transitions:,}")
    if ep_eng:
        print(f"Epistemic Atoms: {len(ep_eng.atoms)} | Notice Board Posts: {ep_eng.total_notice_board_posts} | Board Reads: {ep_eng.total_notice_board_reads} | Priming Recalls: {ep_eng.total_priming_recalls}")
    if club_eng:
        print(f"Club Conclaves: {club_eng.total_club_gatherings_count} | Guest Trials: {club_eng.total_guests_participated_count} | Inductions: {club_eng.total_inductions_count}")
    if game_eng:
        print(f"Games Contested: {game_eng.total_contests_played} | Wagers Circulated: {game_eng.total_wagers_circulated_gold:.2f}g")
    aid_eng = engine.context.get_service("fraternal_aid_engine")
    if aid_eng:
        parish = aid_eng.lodges.get("aid_sacred_hearth_alms")
        p_bal = parish.treasury_balance if parish else 0.0
        print(f"Mutual Aid Dues & Levies Collected: {aid_eng.total_dues_collected_gold:.2f}g | Parish Alms Chest: {p_bal:.2f}g")
    vol_eng = engine.context.get_service("means_end_volition_engine")
    if vol_eng:
        t = vol_eng.get_telemetry()
        print(f"Means-End Volition: Compensatory Actions: {t['total_compensatory_actions']:,} | Transgressive Actions: {t['total_transgressive_actions']:,} | Study Hours: {t['total_aspirational_study_hours']:,}")
        print(f"  Food Borrowed: {t['total_food_borrowing_events']} | Foraged Scraps: {t['total_foraging_events']} | Shoplifting: {t['total_shoplifting_events']} | Active Aspirations: {t['active_aspirations_count']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--adaptive", action="store_true", help="Use Hierarchical Asynchronous Adaptive Event Leaping (HAEST)")
    parser.add_argument("--scenario", type=str, default="oakwood_baseline.json")
    args = parser.parse_args()
    run(days=args.days, scenario=args.scenario, seed=args.seed, stochastic=args.stochastic, adaptive=args.adaptive)
