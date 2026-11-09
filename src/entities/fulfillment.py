"""Multi-dimensional human fulfillment profile."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

class FulfillmentType(Enum):
    HEDONIC_PLEASURE = "HEDONIC_PLEASURE"
    EUDAIMONIC_PURPOSE = "EUDAIMONIC_PURPOSE"
    RELATIONAL_BELONGING = "RELATIONAL_BELONGING"
    CIVIC_ESTEEM = "CIVIC_ESTEEM"
    SPIRITUAL_SERENITY = "SPIRITUAL_SERENITY"

@dataclass
class FulfillmentProfile:
    hedonic_pleasure: float = 50.0
    eudaimonic_purpose: float = 50.0
    relational_belonging: float = 50.0
    civic_esteem: float = 50.0
    spiritual_serenity: float = 50.0

    @property
    def composite_fulfillment(self) -> float:
        return round((self.hedonic_pleasure + self.eudaimonic_purpose + self.relational_belonging + self.civic_esteem + self.spiritual_serenity) / 5.0, 1)

    def adjust(self, fulfillment_type: FulfillmentType, delta: float) -> float:
        attr_map = {
            FulfillmentType.HEDONIC_PLEASURE: "hedonic_pleasure",
            FulfillmentType.EUDAIMONIC_PURPOSE: "eudaimonic_purpose",
            FulfillmentType.RELATIONAL_BELONGING: "relational_belonging",
            FulfillmentType.CIVIC_ESTEEM: "civic_esteem",
            FulfillmentType.SPIRITUAL_SERENITY: "spiritual_serenity",
        }
        attr = attr_map.get(fulfillment_type)
        if attr:
            curr = getattr(self, attr, 50.0)
            new_val = max(0.0, min(100.0, curr + delta))
            setattr(self, attr, new_val)
            return new_val
        return 50.0

    def decay_daily_homeostasis(self, hardship_drag: float = 0.0) -> None:
        decay_rate = 0.05 + hardship_drag
        for attr in ("hedonic_pleasure", "eudaimonic_purpose", "relational_belonging", "civic_esteem", "spiritual_serenity"):
            curr = getattr(self, attr)
            if curr > 50.0:
                setattr(self, attr, max(50.0, curr - decay_rate))
            elif curr < 50.0:
                setattr(self, attr, min(50.0, curr + 0.02))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hedonic_pleasure": round(self.hedonic_pleasure, 1),
            "eudaimonic_purpose": round(self.eudaimonic_purpose, 1),
            "relational_belonging": round(self.relational_belonging, 1),
            "civic_esteem": round(self.civic_esteem, 1),
            "spiritual_serenity": round(self.spiritual_serenity, 1),
            "composite": self.composite_fulfillment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FulfillmentProfile":
        return cls(
            hedonic_pleasure=float(data.get("hedonic_pleasure", 50.0)),
            eudaimonic_purpose=float(data.get("eudaimonic_purpose", 50.0)),
            relational_belonging=float(data.get("relational_belonging", 50.0)),
            civic_esteem=float(data.get("civic_esteem", 50.0)),
            spiritual_serenity=float(data.get("spiritual_serenity", 50.0))
        )
