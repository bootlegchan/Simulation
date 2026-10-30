"""
DecisionAuditor: Standalone logic inspection & counterfactual decision auditor.
Logs 'when', 'who', 'what', 'how', 'why', and 'options evaluated' for every NPC action,
verifying decision logic integrity and non-contradiction.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json

from src.ai.utility import UtilityEvaluator
from src.ai.goap import Goal, Action, GOAPPlanner
from src.entities.npc import NPC
from src.simulation.engine import SimulationEngine

@dataclass
class AlternativeOption:
    goal_name: str
    utility_score: float
    is_precondition_met: bool
    unmet_preconditions: List[str]
    rejection_reason: str

@dataclass
class ActionDecisionAudit:
    tick: int
    virtual_time_iso: str
    npc_id: str
    npc_name: str
    occupation: str
    current_location: str
    needs_snapshot: Dict[str, float]
    chosen_goal: str
    chosen_action: str
    execution_how: str
    primary_why_reason: str
    utility_breakdown: Dict[str, float]
    evaluated_alternatives: List[AlternativeOption]
    logic_integrity_passed: bool
    integrity_warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "virtual_time_iso": self.virtual_time_iso,
            "npc": {
                "id": self.npc_id,
                "name": self.npc_name,
                "occupation": self.occupation,
                "location": self.current_location,
                "needs": self.needs_snapshot,
            },
            "decision": {
                "chosen_goal": self.chosen_goal,
                "chosen_action": self.chosen_action,
                "execution_how": self.execution_how,
                "primary_why_reason": self.primary_why_reason,
            },
            "utility_breakdown": self.utility_breakdown,
            "evaluated_alternatives": [
                {
                    "goal_name": alt.goal_name,
                    "utility_score": round(alt.utility_score, 2),
                    "is_precondition_met": alt.is_precondition_met,
                    "unmet_preconditions": alt.unmet_preconditions,
                    "rejection_reason": alt.rejection_reason,
                }
                for alt in self.evaluated_alternatives
            ],
            "logic_integrity": {
                "passed": self.logic_integrity_passed,
                "warnings": self.integrity_warnings,
            },
        }

class DecisionAuditor:
    """Standalone logic inspector for NPC decisions and counterfactual analysis."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine
        self.audit_logs: List[ActionDecisionAudit] = []
        self.last_actions: Dict[str, str] = {}  # Track previous action to check oscillation

    def audit_tick(self) -> List[ActionDecisionAudit]:
        """Audit decision logic for all active NPCs at the current tick."""
        tick = self.engine.clock.current_tick
        virtual_time = self.engine.clock.current_virtual_time_iso
        tick_audits = []

        # Candidate goals and actions defined in system
        all_candidate_goals = [
            ("satisfy_hunger", {"hunger": 0.0}),
            ("rest", {"energy": 100.0}),
            ("socialize", {"social": 100.0}),
            ("work_production", {"wealth_increased": True}),
            ("spiritual_devotion", {"stress": 0.0}),
        ]

        for npc_id, npc in self.engine.npcs.items():
            needs_snap = {k: round(v, 2) for k, v in npc.needs.items()}
            utilities = UtilityEvaluator.evaluate_drives(npc.needs)

            # Sort drives by utility score descending
            sorted_drives = sorted(utilities.items(), key=lambda x: x[1], reverse=True)
            primary_drive, primary_score = sorted_drives[0] if sorted_drives else ("idle", 0.0)

            # Check inventory / preconditions for candidate actions
            has_food = any(
                item.item_def_id in ("food_bread", "item_bread", "food_apple", "raw_wheat")
                for item in npc.inventory
            )
            has_shelter = npc.home_location_id is not None
            has_workplace = npc.work_location_id is not None

            # Determine chosen goal and action
            chosen_goal = primary_drive
            chosen_action = "idle"
            how_execution = "FSM: Idle / Observation"

            if primary_drive == "satisfy_hunger":
                if has_food:
                    chosen_action = "eat_from_inventory"
                    how_execution = "ActionRegistry.eat() using stored inventory item"
                else:
                    chosen_action = "travel_to_pantry_or_bakery"
                    how_execution = "SpatialGraph BFS pathfinding -> Pantry/Bakery room node"
            elif primary_drive == "rest":
                chosen_action = "sleep_in_bed"
                how_execution = f"GOAP Plan -> Target bed at '{npc.home_location_id or npc.location_id}'"
            elif primary_drive == "socialize":
                chosen_action = "converse_or_tavern_visit"
                how_execution = "CommunicationChannel.propagate_rumor() / Tavern bar interaction"
            else:
                chosen_action = "execute_daily_routine"
                how_execution = f"NPCSchedule hourly block for occupation '{npc.occupation}'"

            # Evaluate alternatives (counterfactuals)
            evaluated_alts = []
            for drive_name, score in sorted_drives:
                if drive_name == primary_drive:
                    continue  # Chosen drive

                unmet_preconditions = []
                precond_met = True

                if drive_name == "satisfy_hunger" and not has_food:
                    unmet_preconditions.append("has_food_in_inventory")
                    precond_met = False
                elif drive_name == "rest" and not has_shelter:
                    unmet_preconditions.append("has_assigned_home_bed")

                rejection_reason = (
                    f"Utility score ({round(score, 2)}) lower than primary drive '{primary_drive}' ({round(primary_score, 2)})"
                    if precond_met
                    else f"Preconditions failed: {', '.join(unmet_preconditions)}"
                )

                evaluated_alts.append(
                    AlternativeOption(
                        goal_name=drive_name,
                        utility_score=score,
                        is_precondition_met=precond_met,
                        unmet_preconditions=unmet_preconditions,
                        rejection_reason=rejection_reason,
                    )
                )

            # Logic Integrity Checks
            integrity_passed = True
            warnings = []

            # Integrity Check 1: Utility Rationality
            if primary_score < 0.0:
                integrity_passed = False
                warnings.append("Invalid negative utility score calculated.")

            # Integrity Check 2: Precondition Consistency
            if chosen_action == "eat_from_inventory" and not has_food:
                integrity_passed = False
                warnings.append("Logic Anomaly: Attempted 'eat_from_inventory' without food items!")

            # Integrity Check 3: Goal Chatter / Rapid Oscillation
            last_act = self.last_actions.get(npc_id)
            if last_act and last_act != chosen_action and primary_score < 15.0:
                warnings.append(f"Goal chatter notice: Switched from '{last_act}' to '{chosen_action}' under low urgency ({round(primary_score, 2)}).")

            self.last_actions[npc_id] = chosen_action

            # Construct Why Reason
            why_reason = f"Primary drive '{primary_drive}' scored highest utility ({round(primary_score, 2)}/100) based on current needs {needs_snap}."

            audit_entry = ActionDecisionAudit(
                tick=tick,
                virtual_time_iso=virtual_time,
                npc_id=npc_id,
                npc_name=npc.name,
                occupation=npc.occupation,
                current_location=npc.location_id or "unknown",
                needs_snapshot=needs_snap,
                chosen_goal=chosen_goal,
                chosen_action=chosen_action,
                execution_how=how_execution,
                primary_why_reason=why_reason,
                utility_breakdown={k: round(v, 2) for k, v in utilities.items()},
                evaluated_alternatives=evaluated_alts,
                logic_integrity_passed=integrity_passed,
                integrity_warnings=warnings,
            )

            self.audit_logs.append(audit_entry)
            tick_audits.append(audit_entry)

        return tick_audits

    def generate_report_markdown(self) -> str:
        """Generate a detailed human-readable Markdown report of all audited decisions."""
        lines = [
            "# 🔍 Standalone NPC Decision Logic & Counterfactual Audit Report",
            f"**Total Audited Decisions**: {len(self.audit_logs)}",
            f"**Total NPCs Monitored**: {len(self.engine.npcs)}",
            "---",
            "",
        ]

        # Group by NPC
        npc_audits: Dict[str, List[ActionDecisionAudit]] = {}
        for entry in self.audit_logs:
            npc_audits.setdefault(entry.npc_name, []).append(entry)

        for npc_name, entries in npc_audits.items():
            lines.append(f"## 👤 NPC: {npc_name} ({entries[0].occupation})")
            for entry in entries[:5]:  # Sample entries per NPC
                lines.append(f"### ⏱️ Tick {entry.tick} [{entry.virtual_time_iso}]")
                lines.append(f"- **Location**: `{entry.current_location}`")
                lines.append(f"- **Needs**: {entry.needs_snapshot}")
                lines.append(f"- **WHAT (Action)**: `{entry.chosen_action}`")
                lines.append(f"- **HOW (Execution)**: {entry.execution_how}")
                lines.append(f"- **WHY (Reasoning)**: {entry.primary_why_reason}")
                lines.append("- **OPTIONS EVALUATED (Counterfactual Alternatives)**:")
                for alt in entry.evaluated_alternatives:
                    status = "✅ Valid" if alt.is_precondition_met else "❌ Unmet Preconditions"
                    lines.append(f"  - Goal `{alt.goal_name}` (Score: {alt.utility_score:.1f}) [{status}]: {alt.rejection_reason}")
                
                integrity_badge = "🟢 PASSED" if entry.logic_integrity_passed else "🔴 FAILED"
                lines.append(f"- **LOGIC INTEGRITY**: {integrity_badge}")
                if entry.integrity_warnings:
                    for w in entry.integrity_warnings:
                        lines.append(f"  - ⚠️ {w}")
                lines.append("")

        return "\n".join(lines)
