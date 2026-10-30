"""
Reflection Engine: Stanford Generative Agents & DeepMind Concordia inspired memory reflection.
Synthesizes high-salience episodic memories into abstract higher-level semantic beliefs.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.npc.memory import MemorySystem, MemoryEntry, SemanticBelief

@dataclass
class ReflectionInsight:
    insight_id: str
    npc_id: str
    tick: int
    abstract_claim: str
    supporting_memory_ids: List[str]
    importance_score: float

class ReflectionEngine:
    """Evaluates memory importance thresholds and generates abstract reflections."""

    @staticmethod
    def calculate_memory_importance(memory: MemoryEntry) -> float:
        """Calculate importance score based on salience and event type."""
        base_importance = memory.emotional_salience * 10.0
        if memory.event_type in ("affair_exposed", "burglary_executed", "crime_witnessed", "mental_break"):
            base_importance += 30.0
        elif memory.event_type in ("courtship_attempt", "trade_executed", "bribe_offered"):
            base_importance += 15.0
        return min(100.0, base_importance)

    @staticmethod
    def evaluate_and_trigger_reflection(
        npc_id: str,
        memory_system: MemorySystem,
        current_tick: int,
        importance_threshold: float = 100.0
    ) -> Optional[ReflectionInsight]:
        """Triggers reflection when cumulative unreflected memory importance exceeds threshold."""
        recent_memories = memory_system.memories[-10:] if memory_system.memories else []
        if not recent_memories:
            return None

        total_importance = sum(ReflectionEngine.calculate_memory_importance(m) for m in recent_memories)

        if total_importance >= importance_threshold:
            top_mems = sorted(recent_memories, key=lambda m: m.emotional_salience, reverse=True)[:3]
            mem_ids = [m.memory_id for m in top_mems]
            subjects = list(set(m.subject_id for m in top_mems if m.subject_id))
            primary_subject = subjects[0] if subjects else "the community"

            abstract_claim = f"{npc_id} reflected on recent events and realized that relations with {primary_subject} require strategic caution."
            
            insight_id = f"refl_{current_tick}_{npc_id}"
            insight = ReflectionInsight(
                insight_id=insight_id,
                npc_id=npc_id,
                tick=current_tick,
                abstract_claim=abstract_claim,
                supporting_memory_ids=mem_ids,
                importance_score=total_importance
            )

            # Record insight as high-level semantic belief via MemorySystem API
            memory_system.update_semantic_belief(
                fact_key=f"reflection:{primary_subject}",
                knowledge_payload={"insight": abstract_claim, "importance": total_importance},
                confidence_score=0.95,
                source_attribution="internal_reflection",
                current_tick=current_tick
            )

            return insight

        return None
