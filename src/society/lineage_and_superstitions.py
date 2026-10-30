"""
Multi-Generational Kinship, Dowry Marriage Alliances, Celestial Omens, and Moral Panic Scapegoating.
Models formal inter-clan dowry pacts, blood feuds, celestial portents, and superstitious scapegoating.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.item import ItemInstance


@dataclass
class MarriageDowryContract:
    contract_id: str
    suitor_id: str
    bride_id: str
    suitor_clan_head_id: str
    bride_clan_head_id: str
    dowry_asset_type: str
    dowry_value_gold: float
    created_tick: int
    is_executed: bool = False
    is_breached: bool = False


class LineageAllianceEngine:
    """Manages inter-clan marriage contracts, dowry transfers, and alliance blood feuds."""

    def __init__(self, lineage_config: Optional[Dict[str, Any]] = None):
        cfg = (lineage_config or {}).get("lineage_and_dowry", {})
        self.dowry_types = cfg.get("dowry_asset_types", ["GOLD_DOWRY", "WORKSHOP_EQUIPMENT", "HEIRLOOM_JEWELRY", "LAND_RIGHTS"])
        self.prestige_thresholds = cfg.get("marriage_prestige_thresholds", {"PATRICIAN_ALLIANCE": 80.0, "BURGHER_ALLIANCE": 50.0})
        self.benefits = cfg.get("alliance_benefits", {"inter_family_trust_boost": 40.0, "shared_trade_discount": 0.15})
        self.breach_penalties = cfg.get("breach_penalties", {"feud_animosity_surge": 70.0, "asset_restitution_ratio": 1.25})
        self.contracts: Dict[str, MarriageDowryContract] = {}

    def draft_marriage_dowry_contract(
        self,
        suitor_clan_head: NPC,
        bride_clan_head: NPC,
        suitor: NPC,
        bride: NPC,
        dowry_type: str,
        dowry_amount: float,
        current_tick: int
    ) -> Dict[str, Any]:
        contract_id = f"dowry_{uuid.uuid4().hex[:8]}"
        contract = MarriageDowryContract(
            contract_id=contract_id,
            suitor_id=suitor.id,
            bride_id=bride.id,
            suitor_clan_head_id=suitor_clan_head.id,
            bride_clan_head_id=bride_clan_head.id,
            dowry_asset_type=dowry_type,
            dowry_value_gold=dowry_amount,
            created_tick=current_tick
        )
        self.contracts[contract_id] = contract

        # Add physical contract item to bride's clan head
        item = ItemInstance(
            instance_id=contract_id,
            item_def_id="contract_marriage_dowry",
            freshness=100.0,
            durability=100.0,
            quality=1.0,
            owner_id=bride_clan_head.id,
            metadata={"contract_id": contract_id, "suitor_id": suitor.id, "bride_id": bride.id}
        )
        bride_clan_head.inventory.append(item)

        suitor_clan_head.adjust_feeling("pride", 20.0)
        bride_clan_head.adjust_feeling("pride", 20.0)

        return {
            "success": True,
            "contract_id": contract_id,
            "suitor_id": suitor.id,
            "bride_id": bride.id,
            "dowry_value": dowry_amount
        }

    def execute_marriage_alliance(
        self,
        contract_id: str,
        suitor_clan_head: NPC,
        bride_clan_head: NPC
    ) -> Dict[str, Any]:
        contract = self.contracts.get(contract_id)
        if not contract or contract.is_executed:
            return {"success": False, "reason": "Invalid or already executed contract"}

        # Transfer dowry gold if gold dowry
        if contract.dowry_asset_type == "GOLD_DOWRY":
            if suitor_clan_head.wealth < contract.dowry_value_gold:
                return {"success": False, "reason": "Suitor family has insufficient wealth for dowry pledge"}
            suitor_clan_head.wealth -= contract.dowry_value_gold
            bride_clan_head.wealth += contract.dowry_value_gold

        contract.is_executed = True
        suitor_clan_head.adjust_feeling("contentment", 30.0)
        bride_clan_head.adjust_feeling("contentment", 30.0)

        return {
            "success": True,
            "contract_id": contract_id,
            "alliance_established": True,
            "trust_boost": self.benefits["inter_family_trust_boost"]
        }

    def break_marriage_contract(
        self,
        contract_id: str,
        violator_npc: NPC,
        scorned_clan_head: NPC
    ) -> Dict[str, Any]:
        contract = self.contracts.get(contract_id)
        if not contract or contract.is_breached:
            return {"success": False, "reason": "Invalid or already breached contract"}

        contract.is_breached = True
        scorned_clan_head.adjust_feeling("resentment", self.breach_penalties["feud_animosity_surge"])
        scorned_clan_head.adjust_feeling("stress", 30.0)
        violator_npc.adjust_feeling("guilt", 30.0)

        return {
            "success": True,
            "contract_id": contract_id,
            "feud_triggered": True,
            "scorned_clan_head_id": scorned_clan_head.id,
            "animosity_surge": self.breach_penalties["feud_animosity_surge"]
        }


class SuperstitionOmensEngine:
    """Manages celestial portents, moral panic hysteria, and superstitious scapegoating."""

    def __init__(self, superstition_config: Optional[Dict[str, Any]] = None):
        cfg = (superstition_config or {}).get("superstition_omens", {})
        self.omen_types = cfg.get("omen_types", {
            "BLOOD_MOON": {"name": "Blood-Red Lunar Eclipse", "hysteria_multiplier": 1.6, "primary_scapegoat_target": "cult_members"},
            "UNSEASONAL_FROST": {"name": "Sudden Harvest-Blighting Frost", "hysteria_multiplier": 1.4, "primary_scapegoat_target": "outcasts"},
            "LIVESTOCK_MURRAIN": {"name": "Mysterious Cattle Murrain", "hysteria_multiplier": 1.3, "primary_scapegoat_target": "strangers"},
            "CHIMNEY_BLAZE": {"name": "Spontaneous Rooftop Ember Storm", "hysteria_multiplier": 1.5, "primary_scapegoat_target": "pariahs"}
        })
        self.active_omens: List[Dict[str, Any]] = []

    def trigger_celestial_omen(self, omen_id: str, current_tick: int) -> Dict[str, Any]:
        omen_def = self.omen_types.get(omen_id, {
            "name": "Celestial Portent",
            "hysteria_multiplier": 1.3,
            "primary_scapegoat_target": "outcasts"
        })
        record = {
            "omen_id": omen_id,
            "name": omen_def["name"],
            "hysteria_multiplier": omen_def["hysteria_multiplier"],
            "target_type": omen_def.get("primary_scapegoat_target", "outcasts"),
            "triggered_tick": current_tick
        }
        self.active_omens.append(record)
        return record

    def evaluate_citizen_superstition(self, npc: NPC, active_omen: Dict[str, Any]) -> Dict[str, Any]:
        neuroticism = npc.personality.get("neuroticism", 0.5)
        is_uneducated = npc.education in ("Illiterate", "Basic Literacy")

        paranoia_surge = 20.0 * active_omen["hysteria_multiplier"] * (0.8 + neuroticism * 0.5)
        if is_uneducated:
            paranoia_surge *= 1.3

        npc.adjust_feeling("stress", round(paranoia_surge, 1))
        npc.needs["conviction"] = min(100.0, npc.needs.get("conviction", 50.0) + 15.0)

        return {
            "npc_id": npc.id,
            "omen_id": active_omen["omen_id"],
            "paranoia_surge": round(paranoia_surge, 1),
            "stress_after": npc.get_feeling("stress")
        }

    def designate_superstitious_scapegoat(
        self,
        active_omen: Dict[str, Any],
        suspects: List[NPC]
    ) -> Optional[Dict[str, Any]]:
        """Townspeople identify a scapegoat to blame for the ill omen."""
        target_type = active_omen.get("target_type", "outcasts")

        candidate = None
        for s in suspects:
            if target_type == "outcasts" and s.social_profile.get("social_class") == "OUTCAST":
                candidate = s
                break
            elif target_type == "cult_members" and hasattr(s, "moral_erosion"):
                score = s.moral_erosion.erosion_score if hasattr(s.moral_erosion, "erosion_score") else float(s.moral_erosion)
                if score > 30.0:
                    candidate = s
                    break
            elif target_type == "pariahs" and s.social_profile.get("is_shunned", False):
                candidate = s
                break

        if not candidate and suspects:
            candidate = suspects[0]

        if candidate:
            candidate.adjust_feeling("stress", 35.0)
            candidate.adjust_feeling("resentment", 30.0)
            return {
                "scapegoat_npc_id": candidate.id,
                "scapegoat_name": candidate.name,
                "omen_id": active_omen["omen_id"],
                "blame_reason": f"Blamed by superstitious citizens for {active_omen['name']}"
            }

        return None
