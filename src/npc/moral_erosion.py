"""
Moral Erosion, Alignment Degradation & Cognitive Dissonance Engine.
Tracks moral erosion, moral alignment drift, and psychological crises of conscience.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class MoralAlignment(Enum):
    VIRTUOUS = "VIRTUOUS"       # 0 - 20 Erosion
    COMPROMISED = "COMPROMISED" # 21 - 50 Erosion
    DEPRAVED = "DEPRAVED"       # 51 - 80 Erosion
    AMORAL = "AMORAL"           # 81 - 100 Erosion

@dataclass
class MoralErosionTracker:
    npc_id: str
    erosion_score: float = 10.0  # 0 (saintly) to 100 (unflinchingly amoral)
    paranoia_score: float = 0.0

    @property
    def alignment(self) -> MoralAlignment:
        if self.erosion_score <= 20.0:
            return MoralAlignment.VIRTUOUS
        elif self.erosion_score <= 50.0:
            return MoralAlignment.COMPROMISED
        elif self.erosion_score <= 80.0:
            return MoralAlignment.DEPRAVED
        else:
            return MoralAlignment.AMORAL

    def advance_erosion(self, amount: float) -> None:
        self.erosion_score = max(0.0, min(100.0, self.erosion_score + amount))
        self.paranoia_score = min(100.0, self.paranoia_score + (amount * 0.5))

    def atone_virtue(self, amount: float) -> None:
        self.erosion_score = max(0.0, self.erosion_score - amount)
        self.paranoia_score = max(0.0, self.paranoia_score - amount)


class CognitiveDissonanceEngine:
    """Evaluates internal moral conflict when an NPC acts against their own core values."""

    @staticmethod
    def evaluate_dissonance_break(npc: NPC, tracker: MoralErosionTracker) -> Dict[str, Any]:
        """
        When a conscientious or honorable NPC commits dark crimes, the clash
        between self-image and actions triggers a severe crisis of conscience.
        """
        honor = npc.social_profile.get("moral_values", {}).get("honor", 0.5)
        conscientiousness = npc.personality.get("conscientiousness", 0.5)
        neuroticism = npc.personality.get("neuroticism", 0.5)

        guilt = npc.get_feeling("guilt")
        stress = npc.get_feeling("stress")

        # High guilt & moral standards trigger cognitive dissonance
        dissonance_pressure = (guilt * 0.6) + (stress * 0.4) + (honor * 30.0) - (tracker.erosion_score * 0.3)

        if dissonance_pressure >= 70.0:
            # Trigger psychological breakdown: Crisis of Conscience
            npc.current_state = "CRISIS_OF_CONSCIENCE"
            npc.adjust_feeling("stress", 20.0)
            npc.adjust_feeling("grief", 25.0)

            return {
                "triggered": True,
                "break_type": "CRISIS_OF_CONSCIENCE",
                "dissonance_pressure": round(dissonance_pressure, 2),
                "description": f"{npc.name} suffered a crushing crisis of conscience, overwhelmed by guilt and moral dissonance."
            }

        return {
            "triggered": False,
            "break_type": None,
            "dissonance_pressure": round(dissonance_pressure, 2)
        }

    @staticmethod
    def execute_penitent_confession(
        penitent: NPC,
        confessor_authority: NPC,
        tracker: MoralErosionTracker
    ) -> Dict[str, Any]:
        """The penitent confesses their crimes to an authority (priest/magistrate), relieving guilt and restoring honor."""
        confessed_guilt = penitent.get_feeling("guilt")
        penitent.set_feeling("guilt", max(0.0, confessed_guilt - 50.0))
        penitent.adjust_feeling("stress", -30.0)
        penitent.adjust_feeling("contentment", 25.0)

        # Regain moral virtue
        tracker.atone_virtue(20.0)
        penitent.current_state = "ABSOLVED_PENITENT"

        return {
            "success": True,
            "penitent_id": penitent.id,
            "confessor_id": confessor_authority.id,
            "guilt_relieved": confessed_guilt - penitent.get_feeling("guilt"),
            "new_alignment": tracker.alignment.value
        }
