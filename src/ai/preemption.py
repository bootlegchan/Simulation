"""Task Preemption Engine with Intelligent Dining Routing."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.economy.intelligent_food_selection import IntelligentFoodSelector, FoodSourceType
from src.behaviours.actions import ActionRegistry

class PreemptionPriority(Enum):
    CRITICAL_BIOLOGICAL_SURVIVAL = 100
    ENVIRONMENTAL_HAZARD = 80
    CIVIC_OR_JUSTICE_COERCION = 70
    PSYCHOLOGICAL_MELTDOWN = 60

@dataclass
class PreemptionEvent:
    npc_id: str
    preempted_action: str
    emergency_action: str
    priority: PreemptionPriority
    reason: str
    tick: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "preempted_action": self.preempted_action,
            "emergency_action": self.emergency_action,
            "priority": self.priority.value,
            "reason": self.reason,
            "tick": self.tick
        }

class TaskPreemptionEngine:
    def __init__(self):
        self.total_preemptions_count: int = 0
        self.preemption_log: List[PreemptionEvent] = []

    def evaluate_preemption(self, npc: NPC, tick: int, context: Any) -> Optional[PreemptionEvent]:
        if not getattr(npc, "is_alive", True):
            return None

        curr_act = getattr(npc, "current_action", "IDLE")
        needs = npc.needs
        feelings = npc.feelings

        # 1. Starvation Emergency (Hunger >= 85.0)
        hunger = needs.get("hunger", 0.0)
        if hunger >= 85.0 and curr_act not in ("BUY_AND_EAT_FOOD", "EAT_FROM_STORES", "FAMINE_RELIEF_EAT"):
            choice = IntelligentFoodSelector.select_best_option(npc, context, emergency_hunger=True)
            new_act = "BUY_AND_EAT_FOOD"
            if choice and choice.source_type == FoodSourceType.INVENTORY_ITEM:
                inv_food = next((i for i in npc.inventory if i.item_def_id == choice.item_def_id), None)
                if inv_food:
                    ActionRegistry.eat(npc, inv_food)
                new_act = "EAT_FROM_STORES"
            elif choice and choice.source_type == FoodSourceType.HOUSEHOLD_PANTRY:
                hh_eng = context.get_service("household_economy_engine") if hasattr(context, "get_service") else None
                if hh_eng and hh_eng.consume_pantry_meal(npc, tick):
                    new_act = "EAT_FROM_STORES"
            elif choice and choice.source_type == FoodSourceType.MUNICIPAL_GRANARY:
                needs["hunger"] = max(0.0, needs.get("hunger", 0.0) - 35.0)
                new_act = "FAMINE_RELIEF_EAT"
            elif choice and choice.price_gold <= npc.wealth and choice.price_gold > 0:
                cost = choice.price_gold
                npc.wealth = max(0.0, round(npc.wealth - cost, 2))
                needs["hunger"] = max(0.0, needs.get("hunger", 0.0) - 45.0)
                new_act = "BUY_AND_EAT_FOOD"
            else:
                # Check parish alms box before falling into unfed starvation distress
                aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
                fed_by_alms = False
                if aid_eng and "aid_sacred_hearth_alms" in aid_eng.lodges:
                    p_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
                    if npc.wealth < 6.0 and p_chest.treasury_balance >= 0.50:
                        p_chest.treasury_balance = round(p_chest.treasury_balance - 0.50, 2)
                        needs["hunger"] = max(0.0, needs.get("hunger", 0.0) - 35.0)
                        new_act = "PARISH_ALMS_EAT"
                        fed_by_alms = True

                if not fed_by_alms:
                    volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
                    resolved = False
                    if volition_eng:
                        sol = volition_eng.execute_sustenance_problem_solving(npc, context, tick)
                        if sol.get("success"):
                            new_act = sol.get("action", "EAT_FROM_STORES")
                            resolved = True
                    if not resolved:
                        npc.adjust_feeling("stress", 15.0)
                        npc.adjust_feeling("contentment", -15.0)
                        new_act = "STARVATION_DISTRESS" 

            evt = PreemptionEvent(npc.id, curr_act, new_act, PreemptionPriority.CRITICAL_BIOLOGICAL_SURVIVAL, f"Severe starvation threat (hunger={hunger:.1f}/100)", tick)
            self._apply(npc, evt, context)
            return evt

        # 2. Critical Exhaustion (Energy <= 10.0)
        energy = needs.get("energy", 100.0)
        if energy <= 10.0 and curr_act not in ("SLEEP_REST", "COLLAPSE_FATIGUE"):
            new_act = "COLLAPSE_FATIGUE" if energy <= 2.0 else "SLEEP_REST"
            ActionRegistry.sleep(npc)
            evt = PreemptionEvent(npc.id, curr_act, new_act, PreemptionPriority.CRITICAL_BIOLOGICAL_SURVIVAL, f"Severe fatigue (energy={energy:.1f}/100)", tick)
            self._apply(npc, evt, context)
            return evt

        # 3. Acute Psychological Meltdown (Stress >= 85.0)
        stress = feelings.get("stress", 0.0)
        if stress >= 85.0 and curr_act not in ("COPING_VENT", "SOLITARY_REST"):
            npc.adjust_feeling("stress", -30.0)
            new_act = "COPING_VENT"
            evt = PreemptionEvent(npc.id, curr_act, new_act, PreemptionPriority.PSYCHOLOGICAL_MELTDOWN, f"Acute stress breakdown (stress={stress:.1f}/100)", tick)
            self._apply(npc, evt, context)
            return evt

        return None

    def _apply(self, npc: NPC, evt: PreemptionEvent, context: Any) -> None:
        npc.current_action = evt.emergency_action
        self.preemption_log.append(evt)
        self.total_preemptions_count += 1
        time_iso = context.clock.current_virtual_time_iso if context and hasattr(context, "clock") and context.clock else f"Tick {evt.tick}"
        npc.record_biographical_entry(evt.tick, time_iso, "TASK_PREEMPTION", evt.reason)
