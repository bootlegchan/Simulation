"""
Cognitive Biases, Subjective Belief Planning, Fog-of-War Expectations, and Habituation Loops.
Models imperfect knowledge, expectation mismatch stress, habit formation, and routine effort discounts.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math

from src.entities.npc import NPC


class SubjectiveCognitionEngine:
    """Manages subjective beliefs about world inventory and expectations vs reality."""

    def __init__(self, cognitive_config: Optional[Dict[str, Any]] = None):
        cfg = (cognitive_config or {}).get("cognitive_biases", {})
        self.staleness_cfg = cfg.get("memory_staleness", {
            "mental_map_decay_half_life_ticks": 4320,
            "confidence_decay_rate_per_day": 0.15
        })
        self.mismatch_cfg = cfg.get("expectation_mismatch", {
            "wasted_trip_stress_surge": 15.0,
            "disappointment_resentment_surge": 12.0,
            "replan_urgency_boost": 25.0
        })
        # Map: npc_id -> { "inventories": { location_id: { item_id: {"qty": int, "recorded_tick": int, "confidence": float} } } }
        self.subjective_beliefs: Dict[str, Dict[str, Any]] = {}

    def record_perceived_inventory(
        self,
        npc_id: str,
        location_id: str,
        item_id: str,
        quantity: int,
        current_tick: int
    ) -> None:
        if npc_id not in self.subjective_beliefs:
            self.subjective_beliefs[npc_id] = {"locations": {}}

        locs = self.subjective_beliefs[npc_id]["locations"].setdefault(location_id, {})
        locs[item_id] = {
            "quantity": quantity,
            "recorded_tick": current_tick,
            "confidence": 1.0
        }

    def evaluate_belief_confidence(
        self,
        npc_id: str,
        location_id: str,
        item_id: str,
        current_tick: int
    ) -> float:
        npc_beliefs = self.subjective_beliefs.get(npc_id, {}).get("locations", {}).get(location_id, {})
        if item_id not in npc_beliefs:
            return 0.0

        rec = npc_beliefs[item_id]
        age_ticks = max(0, current_tick - rec["recorded_tick"])
        half_life = self.staleness_cfg.get("mental_map_decay_half_life_ticks", 4320)
        confidence = rec["confidence"] * math.exp(-0.693 * (age_ticks / max(1, half_life)))
        return round(confidence, 2)

    def verify_expectation_against_reality(
        self,
        npc: NPC,
        location_id: str,
        target_item_id: str,
        actual_inventory_count: int,
        current_tick: int
    ) -> Dict[str, Any]:
        """Compares NPC subjective expectation against actual physical inventory."""
        npc_beliefs = self.subjective_beliefs.get(npc.id, {}).get("locations", {}).get(location_id, {})
        expected_qty = npc_beliefs.get(target_item_id, {}).get("quantity", 0)

        # Update belief with fresh observation
        self.record_perceived_inventory(npc.id, location_id, target_item_id, actual_inventory_count, current_tick)

        if expected_qty > 0 and actual_inventory_count == 0:
            # Expectation failure: wasted trip!
            npc.adjust_feeling("stress", self.mismatch_cfg["wasted_trip_stress_surge"])
            npc.adjust_feeling("resentment", self.mismatch_cfg["disappointment_resentment_surge"])
            return {
                "matched": False,
                "reason": "EXPECTATION_FAILURE_EMPTY_STOCK",
                "expected_quantity": expected_qty,
                "actual_quantity": 0,
                "stress_surge": self.mismatch_cfg["wasted_trip_stress_surge"],
                "replan_recommended": True
            }

        return {
            "matched": True,
            "expected_quantity": expected_qty,
            "actual_quantity": actual_inventory_count,
            "replan_recommended": False
        }


class HabituationEngine:
    """Tracks habit formation, routine action effort discounts, and withdrawal stress."""

    def __init__(self, habit_config: Optional[Dict[str, Any]] = None):
        cfg = (habit_config or {}).get("habituation_system", {})
        self.growth_rate = cfg.get("growth_rate_per_execution", 5.0)
        self.decay_rate = cfg.get("decay_rate_per_day", 2.0)
        self.thresholds = cfg.get("habit_thresholds", {
            "CASUAL": 20.0,
            "ESTABLISHED_ROUTINE": 50.0,
            "COMPULSIVE_ADDICTION": 75.0
        })
        self.utility_modifiers = cfg.get("utility_modifiers", {
            "routine_action_effort_discount": 0.35,
            "addiction_priority_boost": 40.0
        })
        self.withdrawal_effects = cfg.get("withdrawal_effects", {
            "missed_routine_stress_increase": 18.0,
            "missed_addiction_irritability_increase": 35.0
        })
        # Map: npc_id -> { habit_key: float_strength }
        self.habits: Dict[str, Dict[str, float]] = {}

    def record_habit_execution(self, npc_id: str, habit_key: str) -> float:
        npc_habits = self.habits.setdefault(npc_id, {})
        current = npc_habits.get(habit_key, 0.0)
        new_strength = min(100.0, current + self.growth_rate)
        npc_habits[habit_key] = round(new_strength, 1)
        return new_strength

    def get_habit_strength(self, npc_id: str, habit_key: str) -> float:
        return self.habits.get(npc_id, {}).get(habit_key, 0.0)

    def calculate_action_utility_boost(self, npc_id: str, habit_key: str) -> float:
        strength = self.get_habit_strength(npc_id, habit_key)
        if strength >= self.thresholds["COMPULSIVE_ADDICTION"]:
            return self.utility_modifiers["addiction_priority_boost"]
        elif strength >= self.thresholds["ESTABLISHED_ROUTINE"]:
            return round(strength * 0.4, 1)
        return 0.0

    def process_daily_habit_decay_and_withdrawal(self, npc: NPC) -> Dict[str, Any]:
        npc_habits = self.habits.get(npc.id, {})
        withdrawal_surges = []

        for habit_key in list(npc_habits.keys()):
            val = npc_habits[habit_key]
            if val >= self.thresholds["COMPULSIVE_ADDICTION"]:
                npc.adjust_feeling("stress", self.withdrawal_effects["missed_addiction_irritability_increase"])
                npc.adjust_feeling("resentment", 15.0)
                withdrawal_surges.append(habit_key)
            elif val >= self.thresholds["ESTABLISHED_ROUTINE"]:
                npc.adjust_feeling("stress", self.withdrawal_effects["missed_routine_stress_increase"])
                withdrawal_surges.append(habit_key)

            # Decay
            npc_habits[habit_key] = max(0.0, round(val - self.decay_rate, 1))

        return {
            "npc_id": npc.id,
            "withdrawal_habits": withdrawal_surges,
            "active_habits": dict(npc_habits)
        }
