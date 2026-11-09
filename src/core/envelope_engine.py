"""Invertible Bounded Envelope Response Engine."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class EnvelopeEvaluationResult:
    modifier_id: str
    signed_delta: float
    magnitude: float
    is_saturated: bool = False

class BoundedEnvelopeEngine:
    """Evaluates nonlinear bounded envelope stimulus-response transforms."""
    _instance: Optional["BoundedEnvelopeEngine"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = dict(config or {})

    @classmethod
    def get_instance(cls) -> "BoundedEnvelopeEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def evaluate(self, modifier_id: str, npc: Any, stimulus_magnitude: float = 1.0, quality: float = 1.0, **kwargs: Any) -> EnvelopeEvaluationResult:
        delta = float(stimulus_magnitude) * float(quality)
        return EnvelopeEvaluationResult(modifier_id=modifier_id, signed_delta=delta, magnitude=abs(delta))

    def evaluate_inverse(self, modifier_id: str, npc: Any, stimulus_magnitude: float = 1.0, **kwargs: Any) -> EnvelopeEvaluationResult:
        res = self.evaluate(modifier_id, npc, stimulus_magnitude, **kwargs)
        return EnvelopeEvaluationResult(modifier_id=modifier_id, signed_delta=-res.signed_delta, magnitude=res.magnitude)
