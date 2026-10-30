"""
Courtroom Trials, Evidence Analysis & Judicial Sentencing Engine.
Processes reported crimes, conducts trials at the Town Hall, and executes penal sentences.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from src.entities.npc import NPC
from src.society.underworld import CrimeSeverity

class SentenceType(Enum):
    FINE_REPARATIONS = "FINE_REPARATIONS"        # Monetary penalty paid to victim/treasury
    PUBLIC_STOCKADE = "PUBLIC_STOCKADE"          # Placed in Village Square pillory (high public stigma + mockery)
    DUNGEON_DETENTION = "DUNGEON_DETENTION"      # Locked in Guardhouse dungeon cell for duration ticks
    EXILE_BANISHMENT = "EXILE_BANISHMENT"        # Banished from settlement

class JudicialCourtroomEngine:
    """Handles trial proceedings, evidence evaluation, verdict calculation, and sentence execution."""

    def __init__(self):
        self.active_warrants: Dict[str, Dict[str, Any]] = {}
        self.trial_history: List[Dict[str, Any]] = []

    def issue_arrest_warrant(self, crime_record: Dict[str, Any], reporting_npc_id: str) -> Dict[str, Any]:
        """Issues an official law enforcement arrest warrant based on a reported crime."""
        warrant_id = f"warrant_{uuid.uuid4().hex[:8]}"
        warrant = {
            "warrant_id": warrant_id,
            "suspect_id": crime_record["actor_id"],
            "reporting_npc_id": reporting_npc_id,
            "crime_type": crime_record["crime_type"],
            "severity": crime_record["severity"],
            "witness_ids": crime_record.get("witnesses", []),
            "status": "ACTIVE"
        }
        self.active_warrants[warrant_id] = warrant
        return warrant

    def conduct_courtroom_trial(
        self,
        warrant_id: str,
        magistrate: NPC,
        prosecutor_sheriff: NPC,
        accused: NPC,
        witnesses: List[NPC],
        social_network: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """Conducts a formal judicial trial in the Town Hall / Council Chamber."""
        if warrant_id not in self.active_warrants:
            return {"success": False, "reason": "Invalid warrant ID"}

        warrant = self.active_warrants[warrant_id]
        
        # Calculate Prosecution Score based on witness trust and evidence salience
        prosecution_score = 30.0
        for w in witnesses:
            trust_in_witness = social_network.get_bond(magistrate.id, w.id).get_axis("trust")
            prosecution_score += (20.0 + (trust_in_witness * 0.3))

        # Calculate Defense Score based on accused prestige and magistrate relationship
        accused_trust = social_network.get_bond(magistrate.id, accused.id).get_axis("trust")
        defense_score = 20.0 + (accused_trust * 0.4)

        is_guilty = prosecution_score > defense_score

        # Determine Sentence
        sentence_type = SentenceType.FINE_REPARATIONS
        duration_ticks = 0
        fine_amount = 0.0

        if is_guilty:
            if warrant["severity"] == CrimeSeverity.PETTY_ILLEGAL.value:
                if accused.wealth >= 30.0:
                    sentence_type = SentenceType.FINE_REPARATIONS
                    fine_amount = 25.0
                else:
                    sentence_type = SentenceType.PUBLIC_STOCKADE
                    duration_ticks = 1440  # 1 Day in Stockade
            else:  # SEVERE_VIOLENT
                if warrant["crime_type"] in ("arson", "treason"):
                    sentence_type = SentenceType.EXILE_BANISHMENT
                else:
                    sentence_type = SentenceType.DUNGEON_DETENTION
                    duration_ticks = 4320  # 3 Days in Dungeon

            warrant["status"] = "CONVICTED"
        else:
            warrant["status"] = "ACQUITTED"

        trial_record = {
            "trial_id": f"trial_{uuid.uuid4().hex[:8]}",
            "warrant_id": warrant_id,
            "magistrate_id": magistrate.id,
            "accused_id": accused.id,
            "is_guilty": is_guilty,
            "prosecution_score": round(prosecution_score, 2),
            "defense_score": round(defense_score, 2),
            "sentence_type": sentence_type.value if is_guilty else "NONE",
            "fine_amount": fine_amount,
            "duration_ticks": duration_ticks,
            "tick": current_tick
        }

        self.trial_history.append(trial_record)
        return trial_record

    def execute_sentence(
        self,
        trial_record: Dict[str, Any],
        accused: NPC,
        victim: Optional[NPC],
        municipal_treasury: Any,
        stigma_tracker: Any
    ) -> Dict[str, Any]:
        """Executes the legal sentence imposed by the court."""
        if not trial_record["is_guilty"]:
            return {"executed": False, "reason": "Accused was acquitted"}

        sentence = trial_record["sentence_type"]

        if sentence == SentenceType.FINE_REPARATIONS.value:
            paid = min(accused.wealth, trial_record["fine_amount"])
            accused.wealth -= paid
            if victim:
                victim.wealth += (paid * 0.6)  # 60% to victim
            municipal_treasury.deposit_tax(paid * 0.4)  # 40% to town treasury
            return {"executed": True, "sentence": sentence, "fine_paid": paid}

        elif sentence == SentenceType.PUBLIC_STOCKADE.value:
            accused.current_state = "PUBLIC_STOCKADE"
            stigma_tracker.add_stigma(40.0)  # High public stigma
            return {"executed": True, "sentence": sentence, "stigma_added": 40.0}

        elif sentence == SentenceType.DUNGEON_DETENTION.value:
            accused.current_state = "DUNGEON_CELL"
            accused.location_id = "room_dungeon_cell_1"
            return {"executed": True, "sentence": sentence, "dungeon_location": "room_dungeon_cell_1"}

        elif sentence == SentenceType.EXILE_BANISHMENT.value:
            accused.current_state = "EXILED"
            accused.location_id = "OUTSIDE_SETTLEMENT"
            return {"executed": True, "sentence": sentence, "banished": True}

        return {"executed": False, "reason": "Unknown sentence type"}
