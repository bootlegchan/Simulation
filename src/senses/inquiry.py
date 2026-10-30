"""
Conversational Inquiry & Curiosity Engine.
Enables NPCs to actively ask questions during interactions based on personal curiosities and interests,
learning new information and updating their memory and mental map.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.npc.memory import MemorySystem, MemoryEntry

@dataclass
class CuriosityTopic:
    topic_key: str  # e.g., "crime_investigation", "market_pricing", "romance_gossip", "secret_society"
    query_target_id: Optional[str] = None  # Specific NPC or item ID being asked about
    urgency_score: float = 50.0  # 0.0 to 100.0

@dataclass
class InquiryQueryResult:
    question_asked: str
    respondent_id: str
    inquirer_id: str
    topic_key: str
    knowledge_shared: Optional[Dict[str, Any]]
    learned_new_fact: bool
    confidence_score: float
    tick: int

class ConversationalInquiryEngine:
    """Handles interest-driven conversational Q&A and knowledge acquisition between NPCs."""

    @staticmethod
    def evaluate_and_execute_inquiry(
        inquirer: NPC,
        respondent: NPC,
        inquirer_memory: MemorySystem,
        respondent_memory: MemorySystem,
        current_tick: int,
        topic_key: Optional[str] = None
    ) -> InquiryQueryResult:
        """
        Inquirer checks curiosity interests against respondent's memories.
        If respondent possesses matching knowledge, respondent answers and inquirer learns it.
        """
        # Determine topic of interest
        curiosities = inquirer.social_profile.get("curiosities", []) if hasattr(inquirer, "social_profile") and inquirer.social_profile else []
        selected_topic = topic_key or (curiosities[0] if curiosities else "general_town_news")

        # Formulate question
        question_text = f"Have you heard anything regarding '{selected_topic}'?"

        # Search respondent's memory for relevant information
        matching_memories = respondent_memory.query(event_type=selected_topic) if selected_topic != "general_town_news" else respondent_memory.memories

        if not matching_memories and selected_topic != "general_town_news":
            # Fallback search across respondent's memory payloads
            matching_memories = [
                m for m in respondent_memory.memories
                if selected_topic in str(m.payload) or selected_topic in m.event_type
            ]

        if matching_memories:
            # Respondent shares their most recent memory entry on the topic
            shared_memory: MemoryEntry = sorted(matching_memories, key=lambda m: m.tick, reverse=True)[0]
            
            # Inquirer records new memory entry learned from conversation
            learned_memory_id = f"mem_learned_{current_tick}_{inquirer.id}_{shared_memory.memory_id}"
            
            payload = dict(shared_memory.payload)
            payload["source_type"] = "conversational_inquiry"
            payload["source_speaker_id"] = respondent.id
            payload["original_tick"] = shared_memory.tick

            inquirer_memory.record(
                memory_id=learned_memory_id,
                event_type=shared_memory.event_type,
                subject_id=shared_memory.subject_id,
                tick=current_tick,
                payload=payload
            )

            # Update Inquirer's mental map
            if not hasattr(inquirer, "mental_map") or inquirer.mental_map is None:
                inquirer.mental_map = {}
            inquirer.mental_map[f"topic_{selected_topic}"] = {
                "knowledge": payload,
                "learned_from": respondent.id,
                "tick": current_tick
            }

            return InquiryQueryResult(
                question_asked=question_text,
                respondent_id=respondent.id,
                inquirer_id=inquirer.id,
                topic_key=selected_topic,
                knowledge_shared=payload,
                learned_new_fact=True,
                confidence_score=0.85,
                tick=current_tick
            )

        # Respondent has no matching knowledge
        return InquiryQueryResult(
            question_asked=question_text,
            respondent_id=respondent.id,
            inquirer_id=inquirer.id,
            topic_key=selected_topic,
            knowledge_shared=None,
            learned_new_fact=False,
            confidence_score=0.0,
            tick=current_tick
        )
