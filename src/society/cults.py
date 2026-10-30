"""
Clandestine Cults, Esoteric Orders & Inquisition Hysteria Engine.
Models secret subterranean societies, occult rites, dual loyalty conflicts, and moral panic investigations.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.entities.item import ItemInstance

class CultRank(Enum):
    INITIATE = "INITIATE"
    ACOLYTE = "ACOLYTE"
    HIEROPHANT = "HIEROPHANT"

@dataclass
class CultOrder:
    cult_id: str
    name: str
    doctrine: str
    inner_sanctum_room_id: str
    leader_id: str
    members: Dict[str, CultRank] = field(default_factory=dict)
    secrecy_rating: float = 90.0  # 0.0 (exposed) to 100.0 (utterly clandestine)
    sacred_reliquary_item_ids: List[str] = field(default_factory=list)
    rites_conducted_count: int = 0

    def induct_member(self, npc_id: str, rank: CultRank = CultRank.INITIATE) -> None:
        self.members[npc_id] = rank

    def is_member(self, npc_id: str) -> bool:
        return npc_id in self.members


class CultRiteEngine:
    """Manages nocturnal esoteric rites, vows of secrecy, and occult indoctrination."""

    @staticmethod
    def conduct_esoteric_rite(
        cult: CultOrder,
        participants: List[NPC],
        altar_obj: InteractiveObject,
        occult_tome_item: Optional[ItemInstance] = None,
        current_tick: int = 0
    ) -> Dict[str, Any]:
        """
        Executes a clandestine cult ceremony at the subterranean altar.
        Fosters esoteric conviction, mutual bonding, and secrecy, but increases moral erosion and risk of exposure.
        """
        if not altar_obj.has_capability("perform_cult_rite"):
            return {"success": False, "reason": "Altar lacks perform_cult_rite capability"}

        cult.rites_conducted_count += 1
        tome_bonus = 1.3 if (occult_tome_item and occult_tome_item.item_def_id == "item_occult_tome") else 1.0

        for member in participants:
            if not cult.is_member(member.id):
                cult.induct_member(member.id, CultRank.INITIATE)

            # Emotional & psychological impacts
            member.adjust_feeling("passion", round(25.0 * tome_bonus, 1))
            member.adjust_feeling("pride", 15.0)
            member.adjust_feeling("guilt", 15.0)  # Clandestine guilt
            member.needs["social"] = min(100.0, member.needs.get("social", 50.0) + 25.0)
            member.needs["conviction"] = min(100.0, member.needs.get("conviction", 50.0) + 30.0)

            # Advance moral erosion towards amoral alignment
            if hasattr(member, "adjust_moral_erosion"):
                member.adjust_moral_erosion(5.0 * tome_bonus)

        return {
            "success": True,
            "cult_id": cult.cult_id,
            "cult_name": cult.name,
            "participants_count": len(participants),
            "rites_conducted_total": cult.rites_conducted_count,
            "tome_amplified": tome_bonus > 1.0,
            "tick": current_tick
        }


class InquisitionAndHysteriaEngine:
    """Manages town moral panics, inquisitorial investigations, and witch hunts."""

    def __init__(self):
        self.active_inquisitions: Dict[str, Dict[str, Any]] = {}
        self.interrogation_logs: List[Dict[str, Any]] = []

    def trigger_moral_panic(
        self,
        suspected_cult_id: str,
        instigator_npc_id: str,
        evidence_description: str,
        current_tick: int
    ) -> Dict[str, Any]:
        inquisition_id = f"inq_{uuid.uuid4().hex[:8]}"
        record = {
            "inquisition_id": inquisition_id,
            "suspected_cult_id": suspected_cult_id,
            "instigator_id": instigator_npc_id,
            "evidence": evidence_description,
            "hysteria_level": 75.0,  # 0 to 100
            "accused_suspect_ids": [],
            "status": "ACTIVE_INVESTIGATION",
            "start_tick": current_tick
        }
        self.active_inquisitions[inquisition_id] = record
        return record

    def interrogate_suspect(
        self,
        inquisition_id: str,
        inquisitor: NPC,
        suspect: NPC,
        cult: CultOrder,
        current_tick: int,
        pressure_bonus: float = 0.0
    ) -> Dict[str, Any]:
        """Interrogates an accused citizen. High stress or low conscientiousness risks breaking oaths."""
        if inquisition_id not in self.active_inquisitions:
            return {"success": False, "reason": "Unknown inquisition ID"}

        inq = self.active_inquisitions[inquisition_id]
        if suspect.id not in inq["accused_suspect_ids"]:
            inq["accused_suspect_ids"].append(suspect.id)

        is_cultist = cult.is_member(suspect.id)
        willpower = suspect.attributes.get("intelligence", 10.0) + suspect.personality.get("conscientiousness", 0.5) * 20.0
        pressure = inquisitor.attributes.get("strength", 10.0) * 1.5 + (100.0 - suspect.needs.get("energy", 50.0)) * 0.3 + pressure_bonus

        confessed = is_cultist and (pressure > willpower)
        if confessed:
            cult.secrecy_rating = max(0.0, cult.secrecy_rating - 40.0)
            suspect.adjust_feeling("guilt", 40.0)
            suspect.adjust_feeling("stress", 50.0)
        else:
            suspect.adjust_feeling("stress", 35.0)
            suspect.adjust_feeling("resentment", 40.0)

        log_entry = {
            "inquisition_id": inquisition_id,
            "inquisitor_id": inquisitor.id,
            "suspect_id": suspect.id,
            "confessed": confessed,
            "cult_unmasked": confessed,
            "tick": current_tick
        }
        self.interrogation_logs.append(log_entry)
        return log_entry
