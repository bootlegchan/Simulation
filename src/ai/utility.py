import math
from typing import Any, Dict, List, Optional, Tuple
from src.core.randomness import SeededRandom

class UtilityEvaluator:
    """
    Advanced Multi-Objective Utility Evaluator with S-Curves, Emotional Feelings,
    Intimacy Drives, Domestic Dynamics, Vices, Weather, and Softmax Choice Sampling.
    """

    @staticmethod
    def evaluate_drives(
        needs: Dict[str, float],
        personality: Optional[Dict[str, float]] = None,
        emotional_drives: Optional[Dict[str, float]] = None,
        vices: Optional[Dict[str, float]] = None,
        cognition: Optional[Dict[str, Any]] = None,
        env_modifiers: Optional[Dict[str, float]] = None,
        travel_cost: float = 0.0,
        feelings: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        personality = personality or {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
        emotional_drives = emotional_drives or {}
        vices = vices or {}
        cognition = cognition or {"decision_quality": "Rational", "laziness": 0.2}
        env_modifiers = env_modifiers or {}
        feelings = feelings or {}

        utilities: Dict[str, float] = {}

        # 1. Biological Drives
        hunger = needs.get("hunger", 0.0)
        utilities["satisfy_hunger"] = 100.0 / (1.0 + math.exp(-0.08 * (hunger - 50.0)))

        energy = needs.get("energy", 100.0)
        fatigue = 100.0 - energy
        utilities["rest"] = 100.0 / (1.0 + math.exp(-0.08 * (fatigue - 50.0))) + env_modifiers.get("rest", 0.0)

        # 2. Social & Affection Drives
        social_need = needs.get("social", 50.0)
        isolation = 100.0 - social_need
        extraversion_mult = 0.5 + personality.get("extraversion", 0.5)
        utilities["socialize"] = (100.0 / (1.0 + math.exp(-0.06 * (isolation - 40.0)))) * extraversion_mult + env_modifiers.get("socialize", 0.0)

        romance_drive = emotional_drives.get("romance", 0.0)
        libido_drive = emotional_drives.get("libido", 0.0)
        combined_romantic = max(romance_drive, libido_drive)
        if combined_romantic > 0.0:
            utilities["courtship_and_romance"] = 100.0 / (1.0 + math.exp(-0.07 * (combined_romantic - 40.0)))

        # 3. Emotional Feelings Drives (Intimacy, Comfort, Grief, Loneliness, Jealousy)
        passion = feelings.get("passion", 0.0)
        tenderness = feelings.get("tenderness", 0.0)
        loneliness = feelings.get("loneliness", 0.0)
        grief = feelings.get("grief", 0.0)
        jealousy = feelings.get("jealousy", 0.0)
        resentment = feelings.get("resentment", 0.0)

        # Physical Intimacy Drive: surges with passion, tenderness, or loneliness deficit
        intimacy_urgency = max(passion * 0.9, tenderness * 0.8) + (loneliness * 0.4)
        if intimacy_urgency > 20.0:
            utilities["seek_intimacy"] = 100.0 / (1.0 + math.exp(-0.07 * (intimacy_urgency - 40.0)))

        # Comfort and Emotional Soothing Drive: triggered when grieving or partner needs support
        if grief > 25.0 or feelings.get("stress", 0.0) > 40.0:
            comfort_urgency = max(grief, feelings.get("stress", 0.0)) * 0.8 + (tenderness * 0.4)
            utilities["comfort_and_reassurance"] = 100.0 / (1.0 + math.exp(-0.07 * (comfort_urgency - 35.0)))

        # Domestic Hearth Relaxation Drive: family gathering and hearth warmth
        if fatigue > 30.0 or loneliness > 25.0:
            hearth_urgency = (fatigue * 0.5) + (loneliness * 0.4) + (personality.get("agreeableness", 0.5) * 20.0)
            utilities["hearth_relaxation"] = max(0.0, round(hearth_urgency, 2))

        # Diary Reflection & Introspection Drive
        if personality.get("neuroticism", 0.5) > 0.4 and (feelings.get("stress", 0.0) > 20.0 or loneliness > 20.0):
            reflection_urgency = (feelings.get("stress", 0.0) * 0.4) + (loneliness * 0.4) + (personality.get("openness", 0.5) * 20.0)
            utilities["write_diary_reflection"] = max(0.0, round(reflection_urgency, 2))

        # Couple Stroll & Public Affection Drive
        if (tenderness > 20.0 or passion > 20.0) and fatigue < 70.0:
            stroll_urgency = max(tenderness, passion) * 0.7 + (personality.get("extraversion", 0.5) * 20.0)
            utilities["couple_stroll"] = max(0.0, round(stroll_urgency, 2))

        # Flirtation & Romantic Banter Drive
        if (passion > 15.0 or combined_romantic > 20.0) and feelings.get("stress", 0.0) < 60.0:
            flirt_urgency = max(passion, combined_romantic) * 0.8 + (personality.get("extraversion", 0.5) * 25.0)
            utilities["flirt_and_tease"] = max(0.0, round(flirt_urgency, 2))

        # Boundary Discussion & Relationship Clarity Drive
        if (jealousy > 20.0 or resentment > 20.0) and personality.get("conscientiousness", 0.5) > 0.3:
            boundary_urgency = max(jealousy, resentment) * 0.8 + (personality.get("openness", 0.5) * 25.0)
            utilities["discuss_boundaries"] = max(0.0, round(boundary_urgency, 2))

        # Snoop & Intrigue Drive: jealousy, resentment, or curious snooping
        if jealousy > 30.0 or resentment > 30.0 or vices.get("crime_propensity", 0.0) > 30.0:
            snoop_urgency = max(jealousy, resentment) * 0.7 + (vices.get("crime_propensity", 0.0) * 0.5)
            utilities["snoop_and_intrigue"] = max(0.0, round(snoop_urgency, 2))

        # 4. Economic & Labor Drives (Modified by Laziness & Weather)
        conscientiousness = personality.get("conscientiousness", 0.5)
        laziness = cognition.get("laziness", 0.2)
        wealth = needs.get("wealth", 50.0)
        poverty_urgency = max(0.0, 100.0 - wealth)
        work_base = (100.0 / (1.0 + math.exp(-0.05 * (poverty_urgency - 30.0)))) * (0.6 + conscientiousness) * (1.0 - laziness * 0.4)
        utilities["work_production"] = max(0.0, work_base + env_modifiers.get("work_production", 0.0))

        # 5. Psychological Stress & Spiritual Coping
        stress = emotional_drives.get("stress", feelings.get("stress", 0.0))
        neuroticism = personality.get("neuroticism", 0.5)
        if stress > 10.0:
            utilities["spiritual_devotion"] = (100.0 / (1.0 + math.exp(-0.07 * (stress - 40.0)))) * (0.7 + neuroticism) + env_modifiers.get("spiritual_devotion", 0.0)

        # 6. Vices & Illicit Drives (Darker Themes)
        alcohol_dep = vices.get("alcohol_dependence", 0.0)
        gambling_drive = vices.get("gambling_drive", 0.0)
        crime_prop = vices.get("crime_propensity", 0.0)

        if alcohol_dep > 15.0 or gambling_drive > 15.0:
            vice_base = max(alcohol_dep, gambling_drive) * 0.8 + (stress * 0.3)
            if cognition.get("decision_quality") in ("Impulsive", "Short-sighted"):
                vice_base *= 1.3
            utilities["vice_indulgence"] = vice_base + env_modifiers.get("vice_indulgence", 0.0)

        if crime_prop > 25.0 and poverty_urgency > 40.0:
            crime_base = (crime_prop * 0.7) + (poverty_urgency * 0.5)
            if cognition.get("decision_quality") == "Impulsive":
                crime_base *= 1.4
            utilities["crime_illicit"] = crime_base + env_modifiers.get("crime_illicit", 0.0)

        # Apply travel distance penalty
        if travel_cost > 0.0:
            for k in utilities:
                utilities[k] = max(0.0, utilities[k] - (travel_cost * 2.0))

        return {k: max(0.0, round(v, 2)) for k, v in utilities.items()}

    @staticmethod
    def calculate_softmax_probabilities(utilities: Dict[str, float], temperature: float = 10.0) -> Dict[str, float]:
        if not utilities:
            return {"idle": 1.0}
        max_u = max(utilities.values())
        exp_scores = {k: math.exp((u - max_u) / max(1.0, temperature)) for k, u in utilities.items()}
        sum_exp = sum(exp_scores.values())
        return {k: exp / sum_exp for k, exp in exp_scores.items()}

    @staticmethod
    def sample_choice_multinomial_logit(
        utilities: Dict[str, float],
        random_gen: SeededRandom,
        temperature: float = 10.0,
    ) -> Tuple[str, float, Dict[str, float]]:
        probabilities = UtilityEvaluator.calculate_softmax_probabilities(utilities, temperature)
        roll = random_gen.random()
        cumulative = 0.0
        selected = list(utilities.keys())[0]

        for option, prob in probabilities.items():
            cumulative += prob
            if roll <= cumulative:
                selected = option
                break

        return (selected, probabilities[selected], probabilities)
