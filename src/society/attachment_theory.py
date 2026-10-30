"""
Attachment Theory Engine in Multi-Agent Social Simulation.
Implements Bowlby & Ainsworth's Attachment Styles (Secure, Anxious-Preoccupied,
Dismissive-Avoidant, Fearful-Avoidant) to modulate relationship distress,
mate retention, jealousy, and emotional regulation.
"""
from enum import Enum
from typing import Any, Dict, Optional
from src.entities.npc import NPC

class AttachmentStyle(Enum):
    SECURE = "SECURE"
    ANXIOUS_PREOCCUPIED = "ANXIOUS_PREOCCUPIED"
    DISMISSIVE_AVOIDANT = "DISMISSIVE_AVOIDANT"
    FEARFUL_AVOIDANT = "FEARFUL_AVOIDANT"

class AttachmentEngine:
    """Modulates agent emotional responses and relationship behaviors based on attachment style."""

    @staticmethod
    def determine_attachment_style(npc: NPC) -> AttachmentStyle:
        """Determines attachment style from Neuroticism, Agreeableness, and Extraversion."""
        neuroticism = npc.personality.get("neuroticism", 0.5)
        agreeableness = npc.personality.get("agreeableness", 0.5)
        extraversion = npc.personality.get("extraversion", 0.5)

        if neuroticism >= 0.6 and agreeableness < 0.5:
            return AttachmentStyle.FEARFUL_AVOIDANT
        elif neuroticism >= 0.6 and agreeableness >= 0.5:
            return AttachmentStyle.ANXIOUS_PREOCCUPIED
        elif neuroticism < 0.6 and extraversion < 0.4:
            return AttachmentStyle.DISMISSIVE_AVOIDANT
        else:
            return AttachmentStyle.SECURE

    @staticmethod
    def evaluate_relationship_distress(
        npc: NPC,
        neglect_ticks: int,
        suspicion_score: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates emotional stress and behavioral tendency under neglect or suspicion."""
        style = AttachmentEngine.determine_attachment_style(npc)
        base_stress = min(50.0, neglect_ticks * 0.1) + (suspicion_score * 0.5)

        if style == AttachmentStyle.ANXIOUS_PREOCCUPIED:
            # Overreacts to neglect: high anxiety spike, strong urge for reassurance/proximity
            anxiety_spike = base_stress * 1.8
            jealousy_multiplier = 2.0
            behavioral_tendency = "SEEK_REASSURANCE_AND_MONITOR"
        elif style == AttachmentStyle.DISMISSIVE_AVOIDANT:
            # Suppresses distress: low apparent stress, high emotional withdrawal
            anxiety_spike = base_stress * 0.5
            jealousy_multiplier = 0.8
            behavioral_tendency = "WITHDRAW_AND_DECLARE_INDEPENDENCE"
        elif style == AttachmentStyle.FEARFUL_AVOIDANT:
            # Volatile: high distress + push-pull behavior
            anxiety_spike = base_stress * 1.5
            jealousy_multiplier = 1.6
            behavioral_tendency = "PUSH_PULL_CONFLICT"
        else:  # SECURE
            anxiety_spike = base_stress * 1.0
            jealousy_multiplier = 1.0
            behavioral_tendency = "DIRECT_COMMUNICATION"

        return {
            "attachment_style": style.value,
            "calculated_anxiety_stress": round(min(100.0, anxiety_spike), 2),
            "jealousy_multiplier": jealousy_multiplier,
            "behavioral_tendency": behavioral_tendency,
        }
