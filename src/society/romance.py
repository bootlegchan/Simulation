from enum import Enum
from typing import Any, Dict, List, Optional

class RelationshipStage(Enum):
    STRANGER = "STRANGER"
    ACQUAINTANCE = "ACQUAINTANCE"
    FRIEND = "FRIEND"
    CRUSH = "CRUSH"
    COURTING = "COURTING"
    LOVERS = "LOVERS"
    SPOUSES = "SPOUSES"
    RIVALS = "RIVALS"
    ENEMIES = "ENEMIES"
    EXES = "EXES"
    FEUDING = "FEUDING"

class AgreementType(Enum):
    MONOGAMOUS_EXCLUSIVE = "MONOGAMOUS_EXCLUSIVE"
    OPEN_POLYAMOROUS = "OPEN_POLYAMOROUS"
    PLATONIC_COHABITATION = "PLATONIC_COHABITATION"

class AffectionStyle(Enum):
    PHYSICAL_PRESENCE = "PHYSICAL_PRESENCE"
    WORDS_OF_AFFIRMATION = "WORDS_OF_AFFIRMATION"
    ACTS_OF_SERVICE = "ACTS_OF_SERVICE"
    GIFT_GIVING = "GIFT_GIVING"

class InterpersonalBond:
    def __init__(
        self,
        npc_a_id: str,
        npc_b_id: str,
        physical_attraction: float = 50.0,
        romantic_affection: float = 0.0,
        trust: float = 50.0,
        respect: float = 50.0,
        stage: RelationshipStage = RelationshipStage.STRANGER,
        agreement_type: AgreementType = AgreementType.MONOGAMOUS_EXCLUSIVE,
        jealousy_threshold: float = 50.0,
        affection_style: AffectionStyle = AffectionStyle.PHYSICAL_PRESENCE,
        declared_boundaries: Optional[List[str]] = None,
    ):
        self.npc_a_id = npc_a_id
        self.npc_b_id = npc_b_id
        self.physical_attraction = physical_attraction
        self.romantic_affection = romantic_affection
        self.trust = trust
        self.respect = respect
        self.stage = stage
        self.agreement_type = agreement_type
        self.jealousy_threshold = jealousy_threshold
        self.affection_style = affection_style
        self.declared_boundaries = declared_boundaries if declared_boundaries is not None else []

    def calculate_attraction(self, npc_a: Any, npc_b: Any) -> float:
        openness_diff = abs(npc_a.personality.get("openness", 0.5) - npc_b.personality.get("openness", 0.5))
        conscientiousness_diff = abs(npc_a.personality.get("conscientiousness", 0.5) - npc_b.personality.get("conscientiousness", 0.5))
        compatibility = (1.0 - (openness_diff + conscientiousness_diff) / 2.0) * 100.0
        self.physical_attraction = round(compatibility, 1)
        return self.physical_attraction

    def attempt_courtship(self, amount: float = 20.0) -> bool:
        if self.physical_attraction >= 40.0:
            self.romantic_affection = min(100.0, self.romantic_affection + amount)
            if self.romantic_affection >= 50.0:
                self.stage = RelationshipStage.COURTING
            elif self.romantic_affection >= 20.0:
                self.stage = RelationshipStage.CRUSH
            return True
        return False

    def register_infidelity(self, rival_id: str) -> Dict[str, Any]:
        self.trust = -100.0
        self.romantic_affection = 0.0
        self.stage = RelationshipStage.EXES
        return {
            "stage": self.stage,
            "trust": self.trust,
            "jealousy": 100.0,
            "grief": 90.0,
            "rival_id": rival_id
        }

    def evaluate_outside_encounter(
        self,
        rival_id: str,
        is_disclosed: bool = True,
        encounter_type: str = "romantic"
    ) -> Dict[str, Any]:
        """
        Evaluates an outside romantic or physical encounter based on relationship agreements and boundary definitions.
        """
        if self.agreement_type == AgreementType.OPEN_POLYAMOROUS:
            if is_disclosed:
                # Consensual non-monogamy with informed consent generates compersion (sympathetic joy)
                compersion_boost = max(0.0, (100.0 - self.jealousy_threshold) * 0.2)
                self.trust = min(100.0, self.trust + 5.0)
                return {
                    "is_breach": False,
                    "stage": self.stage,
                    "trust": self.trust,
                    "jealousy": 0.0,
                    "compersion": True,
                    "compersion_boost": round(compersion_boost, 1),
                    "rival_id": rival_id,
                    "message": "Encounter is within open polyamorous agreement parameters with full disclosure."
                }
            else:
                # Non-disclosed outside encounter breaches communication boundary
                boundary_trust_penalty = 30.0
                self.trust = max(-100.0, self.trust - boundary_trust_penalty)
                return {
                    "is_breach": True,
                    "stage": self.stage,
                    "trust": self.trust,
                    "jealousy": min(100.0, self.jealousy_threshold * 0.8),
                    "compersion": False,
                    "rival_id": rival_id,
                    "message": "Boundary breach: Outside encounter was concealed rather than openly communicated."
                }
        elif self.agreement_type == AgreementType.PLATONIC_COHABITATION:
            # Platonic cohabitation has no romantic exclusivity claims
            return {
                "is_breach": False,
                "stage": self.stage,
                "trust": self.trust,
                "jealousy": 0.0,
                "compersion": False,
                "rival_id": rival_id,
                "message": "Platonic cohabitation agreement has no romantic exclusivity claims."
            }
        else:
            # Standard monogamous exclusivity: triggers infidelity registration
            res = self.register_infidelity(rival_id)
            res["is_breach"] = True
            res["compersion"] = False
            res["message"] = "Breach of monogamous exclusive agreement: infidelity registered."
            return res

    def discuss_boundaries(
        self,
        new_agreement: AgreementType,
        new_boundaries: List[str]
    ) -> Dict[str, Any]:
        """
        Negotiates and records proactive relationship agreements and boundaries.
        """
        self.agreement_type = new_agreement
        self.declared_boundaries = list(new_boundaries)
        self.trust = min(100.0, self.trust + 15.0)
        return {
            "success": True,
            "agreement_type": self.agreement_type.value,
            "declared_boundaries": self.declared_boundaries,
            "new_trust": self.trust
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_a_id": self.npc_a_id,
            "npc_b_id": self.npc_b_id,
            "physical_attraction": self.physical_attraction,
            "romantic_affection": self.romantic_affection,
            "trust": self.trust,
            "respect": self.respect,
            "stage": self.stage.value,
            "agreement_type": self.agreement_type.value,
            "jealousy_threshold": self.jealousy_threshold,
            "affection_style": self.affection_style.value,
            "declared_boundaries": self.declared_boundaries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterpersonalBond":
        ag_val = data.get("agreement_type", "MONOGAMOUS_EXCLUSIVE")
        aff_val = data.get("affection_style", "PHYSICAL_PRESENCE")
        return cls(
            npc_a_id=data["npc_a_id"],
            npc_b_id=data["npc_b_id"],
            physical_attraction=data.get("physical_attraction", 50.0),
            romantic_affection=data.get("romantic_affection", 0.0),
            trust=data.get("trust", 50.0),
            respect=data.get("respect", 50.0),
            stage=RelationshipStage(data.get("stage", "STRANGER")),
            agreement_type=AgreementType(ag_val),
            jealousy_threshold=data.get("jealousy_threshold", 50.0),
            affection_style=AffectionStyle(aff_val),
            declared_boundaries=data.get("declared_boundaries", []),
        )
