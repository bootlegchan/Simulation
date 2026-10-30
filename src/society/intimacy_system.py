"""
Abstract Behavioral Intimacy & Relationship Mechanics Engine.
Handles non-explicit behavioral drives, privacy evaluations, romantic affection maintenance,
and relationship stage transitions without graphic or explicit content.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.society.romance import InterpersonalBond, RelationshipStage

class RoomPrivacyLevel(Enum):
    PUBLIC = "PUBLIC"          # Market Plaza, Town Square (Privacy: 0.0)
    SEMI_PRIVATE = "SEMI_PRIVATE"  # Tavern Common Room, Chapel Sanctuary (Privacy: 35.0)
    PRIVATE = "PRIVATE"        # Private Residence, Upper Lodging (Privacy: 80.0)
    SECLUDED_LOCK = "SECLUDED_LOCK"  # Locked Master Bedroom, Cellar Vault (Privacy: 100.0)

class PrivacyEvaluator:
    """Evaluates spatial privacy levels for intimate or clandestine social interactions."""

    @staticmethod
    def calculate_room_privacy(
        room_id: str,
        room_type: str,
        is_locked: bool,
        present_occupant_count: int
    ) -> float:
        """
        Calculates room privacy rating (0.0 to 100.0).
        Higher privacy allows intimate bonding and reduces witness exposure risk.
        """
        base_privacy = 20.0
        if "bedroom" in room_id or "lodging" in room_id or "manor" in room_id:
            base_privacy = 80.0
        elif "vault" in room_id or "cellar" in room_id or "sanctuary" in room_id:
            base_privacy = 60.0
        elif "square" in room_id or "plaza" in room_id or "market" in room_id:
            base_privacy = 0.0
        else:
            base_privacy = 35.0

        if is_locked:
            base_privacy = min(100.0, base_privacy + 30.0)

        # Extra witnesses reduce effective privacy
        bystander_count = max(0, present_occupant_count - 2)
        effective_privacy = max(0.0, base_privacy - (bystander_count * 25.0))

        return round(effective_privacy, 1)

class IntimacyDriveManager:
    """
    Manages non-explicit behavioral drives for romantic bonding, affection maintenance,
    and cohabitation relationship satisfaction.
    """

    @staticmethod
    def calculate_intimacy_urgency(npc: NPC, partner_bond: Optional[InterpersonalBond], hour: int) -> float:
        """
        Calculates non-linear utility score for seeking private time or romance with partner.
        Builds up when romantic affection or social drives are unfulfilled.
        """
        if not partner_bond or partner_bond.stage not in (RelationshipStage.LOVERS, RelationshipStage.SPOUSES, RelationshipStage.COURTING):
            return 0.0

        social_need = npc.needs.get("social", 50.0)
        affection_deficit = max(0.0, 100.0 - partner_bond.romantic_affection)
        extraversion = npc.personality.get("extraversion", 0.5)

        night_bonus = 30.0 if (hour >= 21 or hour < 6) else 0.0
        urgency = (affection_deficit * 0.4) + ((100.0 - social_need) * 0.3) + (extraversion * 20.0) + night_bonus

        return round(min(100.0, max(0.0, urgency)), 2)

    @staticmethod
    def execute_romantic_bonding(
        actor: NPC,
        partner: NPC,
        bond: InterpersonalBond,
        room_privacy: float,
        current_tick: int
    ) -> Dict[str, Any]:
        """
        Executes a non-explicit romantic bonding interaction between partners.
        High room privacy increases affection, restores trust, and satisfies social needs.
        """
        if room_privacy < 40.0:
            return {
                "success": False,
                "reason": "Insufficient Privacy (Room too public or witnessed)",
                "affection_gained": 0.0,
                "trust_gained": 0.0
            }

        privacy_mult = room_privacy / 100.0
        affection_gain = round(15.0 * privacy_mult, 1)
        trust_gain = round(5.0 * privacy_mult, 1)

        bond.romantic_affection = min(100.0, bond.romantic_affection + affection_gain)
        bond.trust = min(100.0, bond.trust + trust_gain)

        # Fulfill needs
        actor.needs["social"] = min(100.0, actor.needs.get("social", 50.0) + 25.0)
        partner.needs["social"] = min(100.0, partner.needs.get("social", 50.0) + 25.0)

        # Reduce stress
        if "stress" in actor.needs:
            actor.needs["stress"] = max(0.0, actor.needs["stress"] - 20.0)
        if "stress" in partner.needs:
            partner.needs["stress"] = max(0.0, partner.needs["stress"] - 20.0)

        # Progression check
        if bond.stage == RelationshipStage.COURTING and bond.romantic_affection >= 80.0 and bond.trust >= 60.0:
            bond.stage = RelationshipStage.LOVERS

        return {
            "success": True,
            "actor_id": actor.id,
            "partner_id": partner.id,
            "room_privacy": room_privacy,
            "affection_gained": affection_gain,
            "trust_gained": trust_gain,
            "new_relationship_stage": bond.stage.value,
            "tick": current_tick
        }
