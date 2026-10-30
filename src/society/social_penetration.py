"""
Social Penetration Theory Engine (Altman's Onion Model).
Controls information disclosure depth across disclosure tiers based on trust, privacy rating, and mutual intimacy.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from src.npc.memory import MemorySystem, SemanticBelief

class DisclosureTier(Enum):
    SURFACE_SMALLTALK = "SURFACE_SMALLTALK"  # Tier 1: Weather, public town news
    PERSONAL_OPINIONS = "PERSONAL_OPINIONS"  # Tier 2: Preferences, work complaints
    PRIVATE_VULNERABILITIES = "PRIVATE_VULNERABILITIES"  # Tier 3: Traumas, stress, debts
    CORE_SECRETS_AND_FEARS = "CORE_SECRETS_AND_FEARS"  # Tier 4: Blackmail secrets, affairs, crimes

class SocialPenetrationEngine:
    """Manages progressive information disclosure depth during interactions."""

    @staticmethod
    def evaluate_max_disclosure_tier(
        trust_score: float,
        privacy_rating: float,
        intimacy_score: float = 0.0
    ) -> DisclosureTier:
        """Determines the maximum disclosure tier unlocked by trust, privacy, and intimacy."""
        # Core secrets require high trust (> 70) AND high privacy (> 60)
        if trust_score >= 70.0 and privacy_rating >= 60.0:
            return DisclosureTier.CORE_SECRETS_AND_FEARS
        elif trust_score >= 45.0 and (privacy_rating >= 40.0 or intimacy_score >= 50.0):
            return DisclosureTier.PRIVATE_VULNERABILITIES
        elif trust_score >= 20.0:
            return DisclosureTier.PERSONAL_OPINIONS
        else:
            return DisclosureTier.SURFACE_SMALLTALK

    @staticmethod
    def execute_information_disclosure(
        speaker_id: str,
        listener_id: str,
        speaker_memory: MemorySystem,
        listener_memory: MemorySystem,
        max_unlocked_tier: DisclosureTier,
        current_tick: int
    ) -> Dict[str, Any]:
        """Discloses memories up to the unlocked tier and records mutual vulnerability beliefs."""
        disclosed_facts = []

        if max_unlocked_tier in (DisclosureTier.CORE_SECRETS_AND_FEARS, DisclosureTier.PRIVATE_VULNERABILITIES):
            # Share high-salience memories or secret beliefs
            high_salience = [m for m in speaker_memory.memories if m.emotional_salience >= 5.0]
            if high_salience:
                shared_mem = high_salience[0]
                disclosed_facts.append({
                    "fact_key": f"vulnerability:{shared_mem.event_type}",
                    "payload": shared_mem.payload
                })

                # Listener records learned vulnerability
                listener_memory.update_semantic_belief(
                    fact_key=f"disclosed_vulnerability:{speaker_id}:{shared_mem.event_type}",
                    knowledge_payload=shared_mem.payload,
                    confidence_score=1.0,
                    source_attribution=f"confided_by:{speaker_id}",
                    current_tick=current_tick
                )

        return {
            "speaker_id": speaker_id,
            "listener_id": listener_id,
            "max_unlocked_tier": max_unlocked_tier.value,
            "disclosed_facts_count": len(disclosed_facts),
            "disclosed_facts": disclosed_facts
        }
