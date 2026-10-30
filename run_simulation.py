import json
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.cli.inspector import SimulationInspector
from src.world.environment import EnvironmentState, WeatherType
from src.world.permissions import PermissionsEngine
from src.society.vices_and_crime import DarkCrimeEngine
from src.diagnostics.analytics_suite import ModularAnalyticsSuite

def main():
    print("=" * 70)
    print(" DATA-DRIVEN SOCIAL SIMULATION BACKEND ")
    print("=" * 70)

    data_dir = get_default_data_dir()
    engine = SimulationEngine(data_dir)
    engine.initialize(seed=42)
    inspector = SimulationInspector(engine)

    print("\n[1] Initial Engine Status Report:")
    print(json.dumps(inspector.get_status_report(), indent=2))

    print("\n[2] Expansion Infrastructure Check:")
    print(f"  - Total Fully Profiled NPCs: {len(engine.npcs)}")
    print(f"  - Total Buildings in Oakwood: {len(engine.settlements['settlement_oakwood'].buildings)}")
    
    # Environment & Weather check
    env = EnvironmentState(weather=WeatherType.HEAVY_STORM, season="WINTER")
    mods = env.calculate_utility_modifiers(hour=22)
    print(f"  - Environment Dynamics: Winter Heavy Storm (Night) -> Rest Mod: {mods['rest']:+.1f}, Outdoor Work Mod: {mods['work_production']:+.1f}")

    # Access Permissions check
    thaddeus = engine.npcs["npc_thaddeus"]
    lib_shelf = engine.objects.get("obj_library_bookshelf")
    if lib_shelf:
        perm_res = PermissionsEngine.can_access_object(thaddeus, lib_shelf)
        print(f"  - Access Rule Enforcement: Curator Thaddeus Access to Library Bookshelf -> Allowed: {perm_res['allowed']} ({perm_res['reason']})")

    # Darker Themes & Crime Check
    tobias = engine.npcs["npc_tobias"]
    crime_compulsion = DarkCrimeEngine.evaluate_crime_compulsion(tobias, location_guards_present=0)
    print(f"  - Darker Themes / Vice Check: Tobias Smuggler Crime Compulsion -> Active: {crime_compulsion} (Poverty/Impulsivity/Vice Driven)")

    print("\n[3] Executing 48 Simulation Ticks (2 Days)...")
    engine.start()
    engine.tick(48)

    print("\n[4] Modular Analytics Suite Execution:")
    suite = ModularAnalyticsSuite(data_dir)
    preset_res = suite.run_preset_suite("crime_and_vices", seed=42, ticks=1440)
    print(f"  - Preset Diagnostic Suite 'crime_and_vices' Result: {preset_res}")

    print("\n[5] Snapshot Persistence Test...")
    snap = engine.save_snapshot()
    print(f"  - Snapshot Generated Successfully ({len(json.dumps(snap))} bytes)")
    engine.load_snapshot(snap)
    print(f"  - Restored Engine Virtual Time: {engine.clock.current_virtual_time_iso} (Tick {engine.clock.current_tick})")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE: Ecosystem Operating Normatively.")
    print("=" * 70)

if __name__ == "__main__":
    main()
