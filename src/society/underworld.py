"""
Expanded Underworld, Criminology Spectrum & Illicit Operations Engine.
Models the full spectrum from frowned-upon social taboos to clandestine petty crimes and violent illegal acts.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from src.entities.npc import NPC
from src.entities.item import ItemInstance

class CrimeSeverity(Enum):
    SOCIAL_TABOO = "SOCIAL_TABOO"          # Level 1: Frowned upon (Workplace slacking, public drunkenness, rude insults, gossip)
    PETTY_ILLEGAL = "PETTY_ILLEGAL"        # Level 2: Clandestine petty crimes (Pickpocketing, lockpicking, fence smuggling, bribery)
    SEVERE_VIOLENT = "SEVERE_VIOLENT"      # Level 3: Severe/violent illegal acts (Burglary, blackmail, assault/brawling, arson, treason)

class UnderworldActivityEngine:
    """Manages criminal acts across the full deviance spectrum, recording crime records for law enforcement."""

    @staticmethod
    def execute_social_taboo(
        actor: NPC,
        target: NPC,
        taboo_type: str,  # "workplace_slacking", "public_drunkenness", "rude_insult", "gossip_smear"
        social_network: Any
    ) -> Dict[str, Any]:
        """Level 1: Executes a frowned-upon social taboo. Not illegal, but reduces Respect/Prestige."""
        respect_loss = 15.0
        if taboo_type == "rude_insult":
            respect_loss = 25.0
        elif taboo_type == "public_drunkenness":
            respect_loss = 20.0
            actor.needs["stress"] = max(0.0, actor.needs.get("stress", 50.0) - 15.0)

        # Shift respect negatively in relationship matrix
        bond = social_network.get_bond(target.id, actor.id)
        bond.adjust_axis("respect", -respect_loss)

        return {
            "severity": CrimeSeverity.SOCIAL_TABOO.value,
            "taboo_type": taboo_type,
            "actor_id": actor.id,
            "target_id": target.id,
            "respect_loss": respect_loss,
            "is_illegal": False
        }

    @staticmethod
    def execute_petty_crime(
        actor: NPC,
        victim: NPC,
        crime_type: str,  # "pickpocketing", "lockpicking_trespass", "fence_smuggling", "bribery"
        witness_ids: List[str]
    ) -> Dict[str, Any]:
        """Level 2: Executes a clandestine petty crime. Subject to fines or public stockade if caught."""
        stolen_gold = 0.0
        if crime_type == "pickpocketing" and victim.wealth >= 5.0:
            stolen_gold = min(15.0, victim.wealth * 0.2)
            victim.wealth -= stolen_gold
            actor.wealth += stolen_gold
        elif crime_type == "fence_smuggling":
            stolen_gold = 25.0
            actor.wealth += stolen_gold

        actor.vices["crime_propensity"] = min(100.0, actor.vices.get("crime_propensity", 0.0) + 3.0)
        is_witnessed = len(witness_ids) > 0

        return {
            "crime_id": f"crime_{uuid.uuid4().hex[:8]}",
            "severity": CrimeSeverity.PETTY_ILLEGAL.value,
            "crime_type": crime_type,
            "actor_id": actor.id,
            "victim_id": victim.id,
            "stolen_gold": stolen_gold,
            "is_witnessed": is_witnessed,
            "witnesses": witness_ids,
            "is_illegal": True
        }

    @staticmethod
    def execute_severe_violent_crime(
        actor: NPC,
        victim: NPC,
        crime_type: str,  # "estate_burglary", "extortion_blackmail", "physical_assault", "arson"
        witness_ids: List[str]
    ) -> Dict[str, Any]:
        """Level 3: Executes a severe or violent illegal act. Subject to dungeon detention or banishment."""
        impact_details = {}
        if crime_type == "physical_assault":
            victim.needs["energy"] = max(0.0, victim.needs.get("energy", 50.0) - 40.0)
            victim.needs["stress"] = min(100.0, victim.needs.get("stress", 50.0) + 35.0)
            impact_details["assault_damage"] = 40.0
        elif crime_type == "arson":
            impact_details["building_damaged"] = True
            victim.needs["stress"] = min(100.0, victim.needs.get("stress", 50.0) + 50.0)

        actor.vices["crime_propensity"] = min(100.0, actor.vices.get("crime_propensity", 0.0) + 10.0)
        is_witnessed = len(witness_ids) > 0

        return {
            "crime_id": f"crime_{uuid.uuid4().hex[:8]}",
            "severity": CrimeSeverity.SEVERE_VIOLENT.value,
            "crime_type": crime_type,
            "actor_id": actor.id,
            "victim_id": victim.id,
            "impact_details": impact_details,
            "is_witnessed": is_witnessed,
            "witnesses": witness_ids,
            "is_illegal": True
        }
