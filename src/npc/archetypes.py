from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class NPCArchetypeGrammar:
    """Micro trait correlation grammar and setting-appropriate archetype constraints."""

    @staticmethod
    def validate_npc_profile(npc: NPC) -> Dict[str, Any]:
        """Validates trait correlation bounds and archetype consistency."""
        violations = []
        p = npc.personality
        c = npc.cognition if hasattr(npc, "cognition") and npc.cognition else {}
        v = npc.vices if hasattr(npc, "vices") and npc.vices else {}

        conscientiousness = p.get("conscientiousness", 0.5)
        impulsivity = 1.0 if c.get("decision_quality") == "Impulsive" else 0.3
        crime_propensity = v.get("crime_propensity", 0.0)
        honor = npc.social_profile.get("moral_values", {}).get("honor", 0.5) if hasattr(npc, "social_profile") and npc.social_profile else 0.5

        # Rule 1: High Conscientiousness (>= 0.8) must cap Impulsivity and Crime Propensity (<= 35.0)
        if conscientiousness >= 0.8:
            if crime_propensity > 35.0:
                violations.append(
                    f"Micro Trait Violation for {npc.name}: Conscientiousness ({conscientiousness:.2f}) contradicts high Crime Propensity ({crime_propensity:.1f})."
                )

        # Rule 2: High Honor (>= 0.85) must cap Crime Propensity (<= 30.0)
        if honor >= 0.85 and crime_propensity > 30.0:
            violations.append(
                f"Micro Trait Violation for {npc.name}: High Honor ({honor:.2f}) contradicts high Crime Propensity ({crime_propensity:.1f})."
            )

        # Rule 3: Extreme poverty (< 10.0 gold) with low conscientiousness (< 0.4) cannot be classified as Nobility
        if npc.wealth < 10.0 and conscientiousness < 0.4:
            social_class = npc.social_profile.get("social_class", "LABORER") if hasattr(npc, "social_profile") and npc.social_profile else "LABORER"
            if social_class == "NOBILITY":
                violations.append(
                    f"Micro Class Violation for {npc.name}: Wealth ({npc.wealth:.1f}) and Conscientiousness ({conscientiousness:.2f}) contradict 'NOBILITY' social class."
                )

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "npc_id": npc.id,
            "npc_name": npc.name
        }

    @staticmethod
    def sanitize_and_mutate_npc(npc: NPC) -> NPC:
        """Mutates contradictory randomized traits to ensure societal and psychological coherence."""
        p = npc.personality
        c = npc.cognition if hasattr(npc, "cognition") and npc.cognition else {}
        v = npc.vices if hasattr(npc, "vices") and npc.vices else {}
        sp = npc.social_profile if hasattr(npc, "social_profile") and npc.social_profile else {}

        conscientiousness = p.get("conscientiousness", 0.5)
        honor = sp.get("moral_values", {}).get("honor", 0.5)

        # Fix Rule 1 & 2 contradictions
        if conscientiousness >= 0.8 or honor >= 0.85:
            v["crime_propensity"] = min(25.0, v.get("crime_propensity", 0.0))
            c["decision_quality"] = "Rational"

        npc.vices = v
        npc.cognition = c
        return npc
