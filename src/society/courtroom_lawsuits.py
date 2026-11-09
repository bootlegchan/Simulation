"""Institutional Litigation, Indigent Legal Aid Retainer & Adversarial Trials."""
from dataclasses import dataclass, field
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class LawsuitStatus(str, Enum):
    PENDING = "PENDING"
    CONVICTED = "CONVICTED"
    ACQUITTED = "ACQUITTED"
    DISMISSED = "DISMISSED"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

@dataclass
class LawsuitDefinition:
    lawsuit_type: str
    name: str
    category: str = "CIVIC"
    required_filing_fee_gold: float = 5.0
    evidence_threshold: float = 40.0
    guilty_fine_gold: float = 25.0
    guilty_restitution_gold: float = 0.0
    pillory_hours: int = 0
    victim_pride_restoration: float = 20.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lawsuit_type": self.lawsuit_type,
            "name": self.name,
            "category": self.category,
            "required_filing_fee_gold": self.required_filing_fee_gold,
            "evidence_threshold": self.evidence_threshold,
            "guilty_fine_gold": self.guilty_fine_gold,
            "guilty_restitution_gold": self.guilty_restitution_gold,
            "pillory_hours": self.pillory_hours,
            "victim_pride_restoration": self.victim_pride_restoration,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LawsuitDefinition":
        return cls(
            lawsuit_type=data.get("lawsuit_type", data.get("id", "LAWSUIT")),
            name=data.get("name", "Court Lawsuit"),
            category=data.get("category", "CIVIC"),
            required_filing_fee_gold=float(data.get("required_filing_fee_gold", 5.0)),
            evidence_threshold=float(data.get("evidence_threshold", 40.0)),
            guilty_fine_gold=float(data.get("guilty_fine_gold", 25.0)),
            guilty_restitution_gold=float(data.get("guilty_restitution_gold", 0.0)),
            pillory_hours=int(data.get("pillory_hours", 0)),
            victim_pride_restoration=float(data.get("victim_pride_restoration", 20.0)),
            description=data.get("description", ""),
        )

class LawsuitRegistry:
    _instance: Optional["LawsuitRegistry"] = None

    @classmethod
    def get_instance(cls) -> "LawsuitRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.definitions: Dict[str, LawsuitDefinition] = {
            "SLANDER_AND_DEFAMATION": LawsuitDefinition("SLANDER_AND_DEFAMATION", "Slander and Defamation", required_filing_fee_gold=5.0, evidence_threshold=35.0, guilty_fine_gold=25.0),
            "BREACH_OF_DOWRY_CONTRACT": LawsuitDefinition("BREACH_OF_DOWRY_CONTRACT", "Breach of Dowry Contract", required_filing_fee_gold=10.0, evidence_threshold=50.0, guilty_restitution_gold=40.0),
            "COMMERCIAL_FRAUD_OR_USURY": LawsuitDefinition("COMMERCIAL_FRAUD_OR_USURY", "Commercial Fraud or Usury", required_filing_fee_gold=8.0, evidence_threshold=45.0, guilty_fine_gold=35.0),
        }

    def register_lawsuit(self, definition: LawsuitDefinition) -> None:
        self.definitions[definition.lawsuit_type.upper()] = definition

    def get_lawsuit(self, lawsuit_type: Any) -> Optional[LawsuitDefinition]:
        l_str = lawsuit_type.value if hasattr(lawsuit_type, "value") else str(lawsuit_type)
        return self.definitions.get(l_str.upper())

@dataclass
class LawsuitRecord:
    suit_id: str
    lawsuit_type: str
    plaintiff_id: str
    defendant_id: str
    evidence_score: float
    filing_fee_paid: float
    status: LawsuitStatus
    created_tick: int
    resolved_tick: Optional[int] = None
    verdict_summary: str = ""
    is_indigent_legal_aid: bool = False
    appointed_advocate_id: Optional[str] = None
    advocate_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        st_val = self.status.value if hasattr(self.status, "value") else str(self.status)
        return {
            "suit_id": self.suit_id,
            "lawsuit_type": self.lawsuit_type,
            "plaintiff_id": self.plaintiff_id,
            "defendant_id": self.defendant_id,
            "evidence_score": round(self.evidence_score, 1),
            "filing_fee_paid": self.filing_fee_paid,
            "status": st_val,
            "created_tick": self.created_tick,
            "resolved_tick": self.resolved_tick,
            "verdict_summary": self.verdict_summary,
            "is_indigent_legal_aid": self.is_indigent_legal_aid,
            "appointed_advocate_id": self.appointed_advocate_id,
            "advocate_name": self.advocate_name,
        }

class CourtroomLawsuitEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = dict(config or {})
        self.registry = LawsuitRegistry.get_instance()
        self.active_lawsuits: Dict[str, LawsuitRecord] = {}
        self.trial_history: List[LawsuitRecord] = []

    def file_lawsuit(self, plaintiff: NPC, defendant: NPC, lawsuit_type: str, evidence_score: float, context: Any, current_tick: int) -> Dict[str, Any]:
        l_def = self.registry.get_lawsuit(lawsuit_type)
        fee = l_def.required_filing_fee_gold if l_def else 5.0

        is_indigent = False
        appointed_advocate = None
        treasury = getattr(context, "municipal_treasury", None)

        if plaintiff.wealth < fee or plaintiff.wealth < 12.0:
            advocate = context.find_npc_by_role(["notary", "clerk", "magistrate"])
            if advocate and advocate.id != defendant.id:
                is_indigent = True
                appointed_advocate = advocate
                copay = min(0.50, round(plaintiff.wealth * 0.15, 2))
                plaintiff.wealth = max(0.0, round(plaintiff.wealth - copay, 2))
                fee_paid = copay
                if treasury and hasattr(treasury, "balance") and copay > 0:
                    treasury.balance = round(treasury.balance + copay, 2)
            else:
                return {"success": False, "reason": "Insufficient wealth to cover court filing fee"}
        else:
            fee_paid = fee
            plaintiff.wealth = max(0.0, round(plaintiff.wealth - fee, 2))
            if treasury and hasattr(treasury, "balance"):
                treasury.balance = round(treasury.balance + fee, 2)

        suit_id = f"suit_{uuid.uuid4().hex[:8]}"
        rec = LawsuitRecord(
            suit_id=suit_id,
            lawsuit_type=lawsuit_type,
            plaintiff_id=plaintiff.id,
            defendant_id=defendant.id,
            evidence_score=evidence_score,
            filing_fee_paid=fee_paid,
            status=LawsuitStatus.PENDING,
            created_tick=current_tick,
            is_indigent_legal_aid=is_indigent,
            appointed_advocate_id=appointed_advocate.id if appointed_advocate else None,
            advocate_name=appointed_advocate.name if appointed_advocate else None
        )
        self.active_lawsuits[suit_id] = rec
        return {"success": True, "suit_id": suit_id, "lawsuit": rec.to_dict(), "indigent_legal_aid": is_indigent}

    def conduct_court_trial(self, suit_id: str, magistrate: NPC, context: Any, current_tick: int) -> Dict[str, Any]:
        rec = self.active_lawsuits.get(suit_id)
        if not rec:
            return {"success": False, "reason": "Not found"}

        l_def = self.registry.get_lawsuit(rec.lawsuit_type)
        threshold = l_def.evidence_threshold if l_def else 40.0
        plaintiff = context.npcs.get(rec.plaintiff_id)
        defendant = context.npcs.get(rec.defendant_id)

        defense_score = 0.0
        if defendant:
            d_comp = float(defendant.mental_attributes.get("composure", 50.0))
            d_honor = float(defendant.social_profile.get("moral_values", {}).get("honor", 0.5))
            defense_score += (d_comp * 0.25) + (d_honor * 20.0)

        # Check for submitted epistemic evidence atoms (investigation clues, ledgers, eyewitness facts)
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
        epistemic_evidence_boost = 0.0
        submitted_evidence_titles: List[str] = []

        if ep_eng and defendant:
            from src.society.epistemic_engine import EpistemicStatus, VisibilityTier, CarrierType
            search_participants = [p for p in (plaintiff, magistrate) if p]
            for person in search_participants:
                traces = ep_eng.npc_memories.get(person.id, {})
                for trace in traces.values():
                    atom = trace.atom
                    is_relevant = (
                        atom.subject_id == defendant.id or
                        atom.actor_id == defendant.id or
                        atom.payload.get("suspect_id") == defendant.id or
                        any(tag in (rec.lawsuit_type.lower(), "crime", "evidence") for tag in atom.tags)
                    )
                    if is_relevant:
                        cred = atom.credibility * (1.0 - atom.distortion)
                        weight = 40.0 if atom.status in (EpistemicStatus.FACT, EpistemicStatus.PRESUMPTION) else 15.0
                        boost = cred * weight * trace.salience
                        epistemic_evidence_boost += boost
                        submitted_evidence_titles.append(atom.title)

        effective_evidence = max(0.0, (rec.evidence_score + epistemic_evidence_boost) - defense_score)
        is_convicted = effective_evidence >= threshold

        rec.resolved_tick = current_tick
        if is_convicted and defendant and plaintiff:
            rec.status = LawsuitStatus.CONVICTED
            defendant.criminal_probation_until_tick = current_tick + 4320
            if hasattr(defendant, "add_status_tag"):
                defendant.add_status_tag("TAG_CONVICTED_CRIMINAL")
            fine = l_def.guilty_fine_gold if l_def else 25.0
            actual_fine = min(fine, defendant.wealth)
            defendant.wealth -= actual_fine
            plaintiff.wealth += actual_fine * 0.7
            if hasattr(context, "municipal_treasury"):
                context.municipal_treasury.balance += actual_fine * 0.3
            rec.verdict_summary = f"Defendant {defendant.name} convicted of {rec.lawsuit_type}; paid {actual_fine:.1f}g fine."
        else:
            rec.status = LawsuitStatus.ACQUITTED
            rec.verdict_summary = f"Defendant {defendant.name if defendant else ''} acquitted of {rec.lawsuit_type} due to strong defense testimony."

        # Register verdict fact atom and publish to Town Hall notice board
        if ep_eng:
            from src.society.epistemic_engine import EpistemicStatus, VisibilityTier, CarrierType
            verdict_atom = ep_eng.create_atom(
                title=f"Court Verdict: {rec.lawsuit_type}",
                content=rec.verdict_summary,
                status=EpistemicStatus.FACT,
                visibility=VisibilityTier.PUBLIC_SETTLEMENT,
                carrier_type=CarrierType.NOTE,
                subject_id=defendant.id if defendant else None,
                actor_id=magistrate.id if magistrate else None,
                location_id="room_town_hall",
                emotional_relevance=1.5,
                created_tick=current_tick,
                tags=["court", "verdict", rec.lawsuit_type.lower(), rec.status.value.lower()],
                associative_keys=["trial", "court", "verdict", rec.lawsuit_type.lower()],
                payload=rec.to_dict()
            )
            public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
            ep_eng.post_to_notice_board(public_plaza, verdict_atom)
            ep_eng.post_to_notice_board("room_town_hall", verdict_atom)

        self.trial_history.append(rec)
        del self.active_lawsuits[suit_id]
        return {"success": True, "verdict": rec.status.value, "summary": rec.verdict_summary, "evidence_atoms_count": len(submitted_evidence_titles)}
