"""Gaussian and Asymmetrical Bell Curve Modifier Engine."""
from dataclasses import dataclass
import math
from typing import Any, Dict, Optional

@dataclass
class BellCurveResponse:
    domain: str
    reference_mu: float
    sigma_left: float
    sigma_right: float
    amplitude: float = 2.2
    min_multiplier: float = 0.15
    is_aggressive: bool = False
    aggressiveness_factor: float = 1.0

    def evaluate(self, x: float) -> float:
        diff = float(x) - self.reference_mu
        sigma = self.sigma_left if diff < 0 else self.sigma_right
        if sigma <= 0.001:
            sigma = 0.001
        z = diff / sigma
        gaussian = math.exp(-0.5 * (z ** 2))
        multiplier = self.min_multiplier + (self.amplitude - self.min_multiplier) * gaussian
        return round(max(self.min_multiplier, min(self.amplitude, multiplier)), 3)

class BellCurveModifierEngine:
    """State-conditioned bell curve response evaluator."""
    _instance: Optional["BellCurveModifierEngine"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = dict((config or {}).get("bell_curve_config", config or {}))

    @classmethod
    def get_instance(cls) -> "BellCurveModifierEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_curve(self, npc: Any, domain: str, input_magnitude: float = 0.0) -> BellCurveResponse:
        neuro = float(npc.personality.get("neuroticism", 0.5)) if hasattr(npc, "personality") else 0.5
        comp = float(npc.mental_attributes.get("composure", 50.0)) if hasattr(npc, "mental_attributes") else 50.0
        agg_score = max(0.5, min(2.5, 1.0 + ((neuro - 0.5) * 0.8) - ((comp - 50.0) / 100.0 * 0.7)))
        width_multiplier = 1.0 / agg_score

        base_mu = 25.0
        base_s_left = 15.0
        base_s_right = 35.0
        amplitude = 2.2

        if domain == "wealth_and_commerce":
            w = float(getattr(npc, "wealth", 50.0))
            base_mu = max(1.0, min(80.0, 5.0 * math.pow(max(1.0, w) / 5.0, 0.2)))
            base_s_left = max(5.0, base_mu * 1.2) if w < 10.0 else 10.0
        elif domain == "physiological_sustenance":
            base_mu = 30.0
            base_s_left = 20.0
            base_s_right = 35.0
            amplitude = 2.0
            hunger = float(npc.needs.get("hunger", 20.0)) if hasattr(npc, "needs") else 20.0
            if hunger > 60.0:
                amplitude *= 1.8
                base_mu = 10.0

        return BellCurveResponse(
            domain=domain,
            reference_mu=round(base_mu, 2),
            sigma_left=round(base_s_left * width_multiplier, 2),
            sigma_right=round(base_s_right * width_multiplier, 2),
            amplitude=round(amplitude, 2),
            min_multiplier=0.15,
            is_aggressive=agg_score > 1.15,
            aggressiveness_factor=round(agg_score, 2)
        )

    def scale_feeling_delta(self, npc: Any, feeling_name: str, base_delta: float, stimulus_magnitude: Optional[float] = None) -> float:
        domain = "wealth_and_commerce" if feeling_name in ("contentment",) else ("social_affection" if feeling_name in ("passion", "tenderness", "loneliness") else "trauma_and_adversity")
        mag = abs(base_delta) if stimulus_magnitude is None else float(stimulus_magnitude)
        curve = self.get_curve(npc, domain, mag)
        return round(base_delta * curve.evaluate(mag), 2)

    def get_descaling_rate(self, npc: Any, feeling_name: str, current_val: float, target_baseline: float, base_rate: float) -> float:
        comp = float(npc.mental_attributes.get("composure", 50.0)) if hasattr(npc, "mental_attributes") else 50.0
        resilience = 0.6 + (comp / 100.0) * 1.3
        return max(0.0001, base_rate * resilience)
