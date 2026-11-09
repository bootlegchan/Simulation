"""Unit Test Suite 69: Dynamic Vocational Work Shifts, Labor Demand & Elastic Overtime."""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.entities.occupations import OccupationRegistry
from src.economy.work_shifts import (
    WorkScheduleType,
    ShiftWindow,
    WorkplaceLaborDemandEngine,
    WorkplaceSurgeRequisition,
)
from src.entities.daily_life_rhythms import DynamicDailyRhythmEngine, DailyRhythmPhase
from src.behaviours.actions import ActionRegistry

class TestDynamicWorkShiftsAndLaborDemand(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_01_vocational_shift_windows_and_schedules(self):
        """Verify that different occupations declare distinct, realistic shifts and schedule types."""
        occ_reg = OccupationRegistry.get_instance()

        guard_shift = occ_reg.get_shift_window("guard")
        self.assertEqual(guard_shift.shift_name, "NIGHT_WATCH")
        self.assertEqual(guard_shift.schedule_type, WorkScheduleType.FULL_TIME)
        self.assertEqual(guard_shift.base_start_hour, 21.0)
        self.assertEqual(guard_shift.standard_duration_hours, 8.0)

        baker_shift = occ_reg.get_shift_window("baker")
        self.assertEqual(baker_shift.shift_name, "EARLY_BAKE")
        self.assertEqual(baker_shift.base_start_hour, 3.0)

        bard_shift = occ_reg.get_shift_window("bard")
        self.assertEqual(bard_shift.schedule_type, WorkScheduleType.PART_TIME)
        self.assertEqual(bard_shift.standard_duration_hours, 5.0)

        clerk_shift = occ_reg.get_shift_window("clerk")
        self.assertEqual(clerk_shift.schedule_type, WorkScheduleType.PART_TIME)

        carpenter_shift = occ_reg.get_shift_window("carpenter")
        self.assertEqual(carpenter_shift.shift_name, "STANDARD_DAY")
        self.assertEqual(carpenter_shift.base_start_hour, 8.0)

    def test_02_midnight_wraparound_shift_detection(self):
        """Verify that ShiftWindow.is_within_shift handles daytime and nocturnal shifts correctly."""
        occ_reg = OccupationRegistry.get_instance()
        guard_shift = occ_reg.get_shift_window("guard")  # 21:00 to 05:00

        self.assertTrue(guard_shift.is_within_shift(22.0))
        self.assertTrue(guard_shift.is_within_shift(2.0))
        self.assertTrue(guard_shift.is_within_shift(4.5))
        self.assertFalse(guard_shift.is_within_shift(12.0))
        self.assertFalse(guard_shift.is_within_shift(18.0))

        carpenter_shift = occ_reg.get_shift_window("carpenter")  # 08:00 to 16:00
        self.assertTrue(carpenter_shift.is_within_shift(10.0))
        self.assertTrue(carpenter_shift.is_within_shift(15.5))
        self.assertFalse(carpenter_shift.is_within_shift(1.0))
        self.assertFalse(carpenter_shift.is_within_shift(23.0))

    def test_03_overtime_eligibility_and_wage_multiplier(self):
        """Verify that working during overtime windows awards overtime wage multiplier."""
        occ_reg = OccupationRegistry.get_instance()
        carpenter_shift = occ_reg.get_shift_window("carpenter")  # 08:00 to 16:00, OT 16:00 to 20:00

        self.assertTrue(carpenter_shift.is_overtime_window(17.0))
        self.assertTrue(carpenter_shift.is_overtime_window(19.5))
        self.assertFalse(carpenter_shift.is_overtime_window(12.0))
        self.assertFalse(carpenter_shift.is_overtime_window(23.0))

        # Test wage multiplier in ActionRegistry.work
        carpenter = self.engine.npcs.get("npc_samuel") or self.engine.npcs["npc_aldous"]
        carpenter.occupation = "Master Carpenter"
        carpenter.wealth = 10.0
        carpenter.needs["energy"] = 80.0

        # Advance engine clock to 17:00 (tick = 17 * 60 = 1020, virtual hour 23 or set tick)
        self.engine.clock.resume()
        # Set tick so virtual time hour is in overtime window (17:00)
        # Clock start is 06:00. 11 hours elapsed = 11 * 60 = 660 ticks -> hour 17:00
        self.engine.clock.advance_tick(660)
        self.assertEqual(self.engine.clock.current_virtual_time.hour, 17)

        earned = ActionRegistry.work(carpenter, self.engine.context)
        # Base wage is 2.5 * 1.1 = ~2.8. Overtime multiplier is 1.4x -> earned should be ~3.9g
        self.assertGreater(earned, 3.2)
        # Biographical log should record OVERTIME
        last_log = carpenter.biographical_log[-1]
        self.assertEqual(last_log["metadata"]["labor_category"], "OVERTIME")
        self.assertEqual(last_log["metadata"]["multiplier"], 1.4)

    def test_04_workplace_surge_sensing_extra_bartenders(self):
        """Verify that tavern patron density triggers dynamic surge labor requisitions (extra bartenders)."""
        demand_eng = WorkplaceLaborDemandEngine.get_instance()
        tavern_room = "room_tavern"

        # Initially 0 patrons -> no surge
        surges_0 = demand_eng.evaluate_workplace_surges(self.engine.context, current_tick=100)
        self.assertEqual(len(surges_0), 0)

        # Move 6 citizens into the tavern room
        test_patrons = list(self.engine.npcs.values())[:6]
        for p in test_patrons:
            p.location_id = tavern_room

        surges_crowded = demand_eng.evaluate_workplace_surges(self.engine.context, current_tick=200)
        self.assertGreaterEqual(len(surges_crowded), 1)
        tavern_surge = surges_crowded[0]
        self.assertIn("Extra Bartender", tavern_surge.job_title)
        self.assertEqual(tavern_surge.hourly_wage_multiplier, 1.5)

        # Find and assign candidate
        candidate = demand_eng.find_available_surge_candidate(tavern_surge, self.engine.context)
        self.assertIsNotNone(candidate)
        self.assertEqual(tavern_surge.assigned_npc_id, candidate.id)

        # When candidate works, they earn surge wage
        earned_surge = ActionRegistry.work(candidate, self.engine.context)
        last_log = candidate.biographical_log[-1]
        self.assertEqual(last_log["metadata"]["labor_category"], "CASUAL_SURGE")
        self.assertEqual(last_log["metadata"]["multiplier"], 1.5)

    def test_05_overtime_acceptance_vs_fatigue_refusal(self):
        """Verify that exhausted workers refuse overtime to preserve stamina, while rested workers accept."""
        demand_eng = WorkplaceLaborDemandEngine.get_instance()
        occ_reg = OccupationRegistry.get_instance()
        shift = occ_reg.get_shift_window("carpenter")

        worker = self.engine.npcs["npc_aldous"]
        worker.wealth = 10.0

        # Rested worker with high stamina
        worker.needs["energy"] = 75.0
        worker.feelings["stress"] = 15.0
        accepts_rested, mult_rested, reason_rested = demand_eng.evaluate_worker_overtime_choice(worker, shift, self.engine.context)
        self.assertTrue(accepts_rested)
        self.assertEqual(mult_rested, 1.4)
        self.assertIn("Accepted overtime", reason_rested)

        # Exhausted worker with critical fatigue
        worker.needs["energy"] = 15.0
        accepts_tired, mult_tired, reason_tired = demand_eng.evaluate_worker_overtime_choice(worker, shift, self.engine.context)
        self.assertFalse(accepts_tired)
        self.assertEqual(mult_tired, 1.0)
        self.assertIn("exhaustion", reason_tired.lower())

    def test_06_dynamic_phase_evaluation_no_rigid_clock(self):
        """Verify that diurnal and nocturnal workers follow dynamic vocational shifts without rigid clock cutoffs."""
        rhythm_eng = DynamicDailyRhythmEngine()

        # Guard (Night shift 21:00 - 05:00)
        guard = self.engine.npcs.get("npc_roderick") or self.engine.npcs["npc_aldous"]
        guard.occupation = "Town Guard"
        guard.needs["energy"] = 75.0

        # At 23:00 (night): Guard is in labor shift, NOT sleeping!
        self.engine.clock.current_tick = 1020  # 06:00 + 17h = 23:00
        guard_phase_night = rhythm_eng.evaluate_current_phase(guard, current_tick=1020, context=self.engine.context)
        self.assertEqual(guard_phase_night, DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT)

        # Baker (Dawn shift 03:00 - 11:00)
        baker = self.engine.npcs["npc_greta"]
        baker.occupation = "Master Baker"
        baker.needs["energy"] = 75.0

        # At 04:00: Baker is in labor shift!
        self.engine.clock.current_tick = 1320  # 06:00 + 22h = 04:00 next day
        baker_phase_dawn = rhythm_eng.evaluate_current_phase(baker, current_tick=1320, context=self.engine.context)
        self.assertEqual(baker_phase_dawn, DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT)

        # Carpenter (Standard day 08:00 - 16:00)
        carpenter = self.engine.npcs["npc_aldous"]
        carpenter.occupation = "Master Carpenter"
        carpenter.needs["energy"] = 75.0

        # At 10:00: Carpenter is in labor shift!
        self.engine.clock.current_tick = 240  # 06:00 + 4h = 10:00
        carpenter_phase_day = rhythm_eng.evaluate_current_phase(carpenter, current_tick=240, context=self.engine.context)
        self.assertEqual(carpenter_phase_day, DailyRhythmPhase.PRODUCTIVE_LABOR_SHIFT)

if __name__ == "__main__":
    unittest.main()
