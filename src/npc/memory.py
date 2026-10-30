"""
Stratified Multi-Store Memory Architecture: Sensory Buffer, Episodic Memory,
Semantic Belief Graph, Associative Retrieval, and Sleep Consolidation.
"""
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class MemoryEntry:
    memory_id: str
    event_type: str
    subject_id: str
    tick: int
    payload: Dict[str, Any]
    emotional_salience: float = 1.0  # 1.0 (mundane) to 10.0 (trauma/crime/romance)
    retention_strength: float = 100.0

@dataclass
class SemanticBelief:
    fact_key: str  # e.g., "location_owner:room_vance_manor", "trust_assessment:npc_tobias"
    knowledge_payload: Dict[str, Any]
    confidence_score: float = 1.0  # 0.0 to 1.0
    source_attribution: str = "direct_observation"  # "direct_observation", "conversation:npc_silas", "rumor"
    last_updated_tick: int = 0

class MemorySystem:
    """
    Stratified Multi-Store Cognitive Memory Architecture for autonomous NPCs.
    Features Sensory Buffer (working memory), Episodic Store (Ebbinghaus decay),
    Semantic Belief Graph, Associative Retrieval Scoring, and Sleep Consolidation.
    """

    def __init__(self, retention_half_life: float = 50.0):
        self.sensory_buffer: List[Dict[str, Any]] = []
        self.memories: List[MemoryEntry] = []  # Episodic Memory Store
        self.semantic_beliefs: Dict[str, SemanticBelief] = {}  # Semantic Memory Graph
        self.retention_half_life = retention_half_life

    def record_sensory_input(self, event_type: str, subject_id: str, tick: int, payload: Dict[str, Any]) -> None:
        """Record raw live sensory input into the immediate Sensory Buffer."""
        self.sensory_buffer.append({
            "event_type": event_type,
            "subject_id": subject_id,
            "tick": tick,
            "payload": payload
        })

    def record(
        self,
        memory_id: str,
        event_type: str,
        subject_id: str,
        tick: int,
        payload: Dict[str, Any],
        salience: float = 1.0
    ) -> None:
        """Record episodic memory entry with emotional salience weighting."""
        self.memories.append(MemoryEntry(memory_id, event_type, subject_id, tick, payload, salience, 100.0))

    def apply_ebbinghaus_decay(self, current_tick: int) -> None:
        """Decay retention strength over time based on emotional salience."""
        retained = []
        for mem in self.memories:
            elapsed = max(0, current_tick - mem.tick)
            decay_rate = 0.693 / (self.retention_half_life * mem.emotional_salience)
            mem.retention_strength = 100.0 * math.exp(-decay_rate * elapsed)
            
            if mem.retention_strength > 5.0:
                retained.append(mem)
        self.memories = retained

    def query(self, event_type: Optional[str] = None, subject_id: Optional[str] = None) -> List[MemoryEntry]:
        """Query episodic memory by event type or subject ID."""
        results = self.memories
        if event_type:
            results = [m for m in results if m.event_type == event_type]
        if subject_id:
            results = [m for m in results if m.subject_id == subject_id]
        return results

    def associative_retrieval_query(
        self,
        query_text: str,
        current_tick: int,
        top_k: int = 5,
        recency_weight: float = 1.0,
        salience_weight: float = 2.0,
        relevance_weight: float = 3.0
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Associative Memory Retrieval Scoring:
        RetrievalScore = w_r * Recency + w_s * Salience + w_k * Relevance
        """
        scored_memories = []
        for mem in self.memories:
            elapsed = max(1, current_tick - mem.tick)
            recency_score = 1.0 / math.log(elapsed + 2.0)
            salience_score = mem.emotional_salience / 10.0
            
            # Simple keyword relevance match across event_type, subject_id, and payload
            mem_str = f"{mem.event_type} {mem.subject_id} {str(mem.payload)}".lower()
            relevance_score = 1.0 if any(k.lower() in mem_str for k in query_text.split()) else 0.1

            total_score = (
                (recency_weight * recency_score) +
                (salience_weight * salience_score) +
                (relevance_weight * relevance_score)
            )
            scored_memories.append((mem, round(total_score, 3)))

        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:top_k]

    def update_semantic_belief(
        self,
        fact_key: str,
        knowledge_payload: Dict[str, Any],
        confidence_score: float = 1.0,
        source_attribution: str = "direct_observation",
        current_tick: int = 0
    ) -> SemanticBelief:
        """Upsert a semantic belief entry in the NPC's semantic memory graph."""
        belief = SemanticBelief(
            fact_key=fact_key,
            knowledge_payload=dict(knowledge_payload),
            confidence_score=confidence_score,
            source_attribution=source_attribution,
            last_updated_tick=current_tick
        )
        self.semantic_beliefs[fact_key] = belief
        return belief

    def consolidate_memories(self, current_tick: int) -> int:
        """
        Sleep/Rest Memory Consolidation:
        Processes raw sensory buffer and high-salience episodic memories into semantic beliefs.
        Clears sensory buffer afterwards.
        """
        consolidated_count = 0

        # Process sensory buffer
        for item in self.sensory_buffer:
            fact_key = f"perceived:{item['event_type']}:{item['subject_id']}"
            self.update_semantic_belief(
                fact_key=fact_key,
                knowledge_payload=item["payload"],
                confidence_score=1.0,
                source_attribution="direct_observation",
                current_tick=current_tick
            )
            consolidated_count += 1

        self.sensory_buffer.clear()

        # Process high-salience episodic memories (salience >= 3.0)
        for mem in self.memories:
            if mem.emotional_salience >= 3.0:
                fact_key = f"episodic_fact:{mem.event_type}:{mem.subject_id}"
                self.update_semantic_belief(
                    fact_key=fact_key,
                    knowledge_payload=mem.payload,
                    confidence_score=min(1.0, mem.emotional_salience / 10.0 + 0.5),
                    source_attribution=mem.payload.get("source_type", "direct_experience"),
                    current_tick=current_tick
                )
                consolidated_count += 1

        return consolidated_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memories": [
                {
                    "memory_id": m.memory_id,
                    "event_type": m.event_type,
                    "subject_id": m.subject_id,
                    "tick": m.tick,
                    "payload": m.payload,
                    "emotional_salience": m.emotional_salience,
                    "retention_strength": m.retention_strength,
                }
                for m in self.memories
            ],
            "semantic_beliefs": {
                k: {
                    "fact_key": b.fact_key,
                    "knowledge_payload": b.knowledge_payload,
                    "confidence_score": b.confidence_score,
                    "source_attribution": b.source_attribution,
                    "last_updated_tick": b.last_updated_tick,
                }
                for k, b in self.semantic_beliefs.items()
            }
        }

    def load_dict(self, data: Any) -> None:
        if isinstance(data, list):
            self.memories = [
                MemoryEntry(
                    memory_id=d["memory_id"],
                    event_type=d["event_type"],
                    subject_id=d["subject_id"],
                    tick=d["tick"],
                    payload=d["payload"],
                    emotional_salience=d.get("emotional_salience", 1.0),
                    retention_strength=d.get("retention_strength", 100.0),
                )
                for d in data
            ]
            self.semantic_beliefs = {}
        elif isinstance(data, dict):
            self.memories = [
                MemoryEntry(
                    memory_id=d["memory_id"],
                    event_type=d["event_type"],
                    subject_id=d["subject_id"],
                    tick=d["tick"],
                    payload=d["payload"],
                    emotional_salience=d.get("emotional_salience", 1.0),
                    retention_strength=d.get("retention_strength", 100.0),
                )
                for d in data.get("memories", [])
            ]
            self.semantic_beliefs = {
                k: SemanticBelief(
                    fact_key=b["fact_key"],
                    knowledge_payload=b["knowledge_payload"],
                    confidence_score=b.get("confidence_score", 1.0),
                    source_attribution=b.get("source_attribution", "direct_observation"),
                    last_updated_tick=b.get("last_updated_tick", 0),
                )
                for k, b in data.get("semantic_beliefs", {}).items()
            }
