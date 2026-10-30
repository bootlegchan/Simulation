"""
Sternberg's Triangular Theory of Love Engine.
Decomposes romantic bonds into Intimacy (closeness/sharing), Passion (attraction/drive),
and Commitment (decision/loyalty), evaluating taxonomy taxonomy and commitment decay.
"""
from enum import Enum
from typing import Any, Dict

class LoveTaxonomy(Enum):
    NON_LOVE = "NON_LOVE"
    LIKING = "LIKING"  # Intimacy only
    INFATUATION = "INFATUATION"  # Passion only
    EMPTY_LOVE = "EMPTY_LOVE"  # Commitment only
    ROMANTIC_LOVE = "ROMANTIC_LOVE"  # Intimacy + Passion
    COMPANIONATE_LOVE = "COMPANIONATE_LOVE"  # Intimacy + Commitment
    FATUOUS_LOVE = "FATUOUS_LOVE"  # Passion + Commitment
    CONSUMMATE_LOVE = "CONSUMMATE_LOVE"  # Intimacy + Passion + Commitment

class TriangularLoveModel:
    """Manages 3-component love taxonomy and commitment dynamics."""

    def __init__(
        self,
        intimacy: float = 0.0,
        passion: float = 0.0,
        commitment: float = 0.0
    ):
        self.intimacy = max(0.0, min(100.0, intimacy))  # Shared closeness & communication
        self.passion = max(0.0, min(100.0, passion))    # Physical attraction & desire
        self.commitment = max(0.0, min(100.0, commitment))  # Formal decision to maintain bond

    def get_love_taxonomy(self) -> LoveTaxonomy:
        """Classifies the relationship based on component threshold combinations (>= 40.0)."""
        has_i = self.intimacy >= 40.0
        has_p = self.passion >= 40.0
        has_c = self.commitment >= 40.0

        if has_i and has_p and has_c:
            return LoveTaxonomy.CONSUMMATE_LOVE
        elif has_i and has_p:
            return LoveTaxonomy.ROMANTIC_LOVE
        elif has_i and has_c:
            return LoveTaxonomy.COMPANIONATE_LOVE
        elif has_p and has_c:
            return LoveTaxonomy.FATUOUS_LOVE
        elif has_i:
            return LoveTaxonomy.LIKING
        elif has_p:
            return LoveTaxonomy.INFATUATION
        elif has_c:
            return LoveTaxonomy.EMPTY_LOVE
        else:
            return LoveTaxonomy.NON_LOVE

    def process_interaction_impact(
        self,
        is_private_bonding: bool,
        shared_disclosure: bool,
        conflict_occurred: bool
    ) -> Dict[str, Any]:
        """Updates love components based on interaction parameters."""
        if is_private_bonding:
            self.passion = min(100.0, self.passion + 15.0)
            self.intimacy = min(100.0, self.intimacy + 10.0)

        if shared_disclosure:
            self.intimacy = min(100.0, self.intimacy + 12.0)
            self.commitment = min(100.0, self.commitment + 5.0)

        if conflict_occurred:
            self.intimacy = max(0.0, self.intimacy - 15.0)
            self.commitment = max(0.0, self.commitment - 10.0)

        return {
            "intimacy": round(self.intimacy, 2),
            "passion": round(self.passion, 2),
            "commitment": round(self.commitment, 2),
            "taxonomy": self.get_love_taxonomy().value
        }

    def process_neglect_decay(self, elapsed_ticks: int) -> None:
        """Decays passion faster than intimacy, and intimacy faster than commitment during neglect."""
        days = elapsed_ticks / 1440.0
        self.passion = max(0.0, self.passion - (days * 5.0))
        self.intimacy = max(0.0, self.intimacy - (days * 2.0))
        # Commitment decays only if intimacy drops below 20.0
        if self.intimacy < 20.0:
            self.commitment = max(0.0, self.commitment - (days * 3.0))
