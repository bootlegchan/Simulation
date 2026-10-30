"""
Goffman's Front Stage vs. Back Stage Social Behavior Engine.
Distinguishes between public impression management (Front Stage) and private uninhibited behavior (Back Stage).
"""
from typing import Any, Dict
from src.entities.npc import NPC

class GoffmanFrontBackStageEngine:
    """Modulates agent behaviors and emotional expression based on spatial node privacy."""

    @staticmethod
    def evaluate_stage_context(privacy_rating: float) -> str:
        """Categorizes current spatial node context into 'FRONT_STAGE' or 'BACK_STAGE'."""
        return "BACK_STAGE" if privacy_rating >= 60.0 else "FRONT_STAGE"

    @staticmethod
    def adjust_behavior_for_context(
        npc: NPC,
        privacy_rating: float,
        proposed_drive: str,
        utility_score: float
    ) -> Dict[str, Any]:
        """
        In Front Stage (public), agents suppress vices, mask illegal intentions,
        and conform to social norms. In Back Stage (private), agents express raw preferences.
        """
        context = GoffmanFrontBackStageEngine.evaluate_stage_context(privacy_rating)
        modified_utility = utility_score
        is_suppressed = False

        if context == "FRONT_STAGE":
            # Suppress vices, crime, or illicit drives in public
            if proposed_drive in ("vice_indulgence", "crime_illicit", "intimacy_bonding"):
                conscientiousness = npc.personality.get("conscientiousness", 0.5)
                suppression_factor = 0.2 + (conscientiousness * 0.6)
                modified_utility = utility_score * (1.0 - suppression_factor)
                is_suppressed = True
        else:  # BACK_STAGE
            # Boost relaxation, secret plans, and uninhibited vice/intimacy drives
            if proposed_drive in ("vice_indulgence", "rest", "intimacy_bonding"):
                modified_utility = utility_score * 1.35

        return {
            "context": context,
            "original_utility": utility_score,
            "modified_utility": round(modified_utility, 2),
            "is_suppressed": is_suppressed
        }
