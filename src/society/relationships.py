from typing import Dict, Any, Optional

class RelationshipAxis:
    TRUST = "trust"  # -100 to +100
    RESPECT = "respect"  # -100 to +100
    ROMANTIC_AFFECTION = "romantic_affection"  # 0 to 100
    PHYSICAL_ATTRACTION = "physical_attraction"  # 0 to 100
    FEAR_INTIMIDATION = "fear_intimidation"  # 0 to 100
    DEBT_OBLIGATION = "debt_obligation"  # 0 to 100
    SHARED_SECRET_TIE = "shared_secret_tie"  # 0 to 100

class MultiAxisRelationship:
    """7-Axis Social Relationship Matrix model."""

    def __init__(self, from_id: str, to_id: str):
        self.from_id = from_id
        self.to_id = to_id
        self.axes: Dict[str, float] = {
            RelationshipAxis.TRUST: 0.0,
            RelationshipAxis.RESPECT: 0.0,
            RelationshipAxis.ROMANTIC_AFFECTION: 0.0,
            RelationshipAxis.PHYSICAL_ATTRACTION: 0.0,
            RelationshipAxis.FEAR_INTIMIDATION: 0.0,
            RelationshipAxis.DEBT_OBLIGATION: 0.0,
            RelationshipAxis.SHARED_SECRET_TIE: 0.0,
        }

    def set_axis(self, axis: str, value: float) -> None:
        if axis in (RelationshipAxis.TRUST, RelationshipAxis.RESPECT):
            self.axes[axis] = max(-100.0, min(100.0, value))
        else:
            self.axes[axis] = max(0.0, min(100.0, value))

    def get_axis(self, axis: str) -> float:
        return self.axes.get(axis, 0.0)

    def adjust_axis(self, axis: str, delta: float) -> float:
        curr = self.get_axis(axis)
        self.set_axis(axis, curr + delta)
        return self.get_axis(axis)

    def get_overall_affinity(self) -> float:
        """Composite relationship score for backward compatibility."""
        trust = self.get_axis(RelationshipAxis.TRUST)
        respect = self.get_axis(RelationshipAxis.RESPECT)
        affection = self.get_axis(RelationshipAxis.ROMANTIC_AFFECTION)
        fear = self.get_axis(RelationshipAxis.FEAR_INTIMIDATION)
        return max(-100.0, min(100.0, (trust * 0.4) + (respect * 0.3) + (affection * 0.3) - (fear * 0.2)))

class SocialNetwork:
    """Directional 7-Axis Relationship Network Engine."""

    def __init__(self):
        self.relationships: Dict[Tuple[str, str], MultiAxisRelationship] = {}

    def get_bond(self, from_id: str, to_id: str) -> MultiAxisRelationship:
        key = (from_id, to_id)
        if key not in self.relationships:
            self.relationships[key] = MultiAxisRelationship(from_id, to_id)
        return self.relationships[key]

    def set_relationship(self, from_id: str, to_id: str, score: float) -> None:
        bond = self.get_bond(from_id, to_id)
        bond.set_axis(RelationshipAxis.TRUST, score)

    def get_relationship(self, from_id: str, to_id: str) -> float:
        key = (from_id, to_id)
        if key in self.relationships:
            return self.relationships[key].get_overall_affinity()
        return 0.0

    def adjust_relationship(self, from_id: str, to_id: str, delta: float) -> float:
        bond = self.get_bond(from_id, to_id)
        bond.adjust_axis(RelationshipAxis.TRUST, delta)
        return bond.get_overall_affinity()
