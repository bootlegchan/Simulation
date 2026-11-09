"""Municipal Income Taxation & Elastic Evasion Engine."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

@dataclass
class TaxAssessmentRecord:
    npc_id: str
    npc_name: str
    actual_earnings_gold: float
    declared_earnings_gold: float
    tax_rate: float
    tax_paid_gold: float
    evaded_gold: float
    was_audited: bool
    audit_penalty_gold: float
    reporting_truthfulness: float
    assessor_id: Optional[str]
    tick: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "actual_earnings_gold": round(self.actual_earnings_gold, 2),
            "declared_earnings_gold": round(self.declared_earnings_gold, 2),
            "tax_rate": self.tax_rate,
            "tax_paid_gold": round(self.tax_paid_gold, 2),
            "evaded_gold": round(self.evaded_gold, 2),
            "was_audited": self.was_audited,
            "audit_penalty_gold": round(self.audit_penalty_gold, 2),
            "reporting_truthfulness": round(self.reporting_truthfulness, 2),
            "assessor_id": self.assessor_id,
            "tick": self.tick,
        }

class MunicipalTaxEngine:
    DEFAULT_INCOME_TAX_RATE: float = 0.08

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        from src.configuration.settings import SettingsRegistry
        gov_cfg = SettingsRegistry.get_instance().get("civic_governance")
        tax_cfg = gov_cfg.get("taxation", {})

        self.config = dict(config or {})
        self.tax_rate = float(self.config.get("income_tax_rate", tax_cfg.get("income_tax_rate", self.DEFAULT_INCOME_TAX_RATE)))
        self.audit_vigilance = float(self.config.get("audit_vigilance", tax_cfg.get("audit_vigilance", 0.12)))
        self.evasion_penalty_multiplier = float(self.config.get("evasion_penalty_multiplier", tax_cfg.get("evasion_penalty_multiplier", 1.5)))
        self.audit_evasion_min_threshold = float(tax_cfg.get("audit_evasion_min_threshold_gold", 0.50))
        self.max_audit_probability = float(tax_cfg.get("max_audit_probability", 0.40))
        self.assessment_history: List[TaxAssessmentRecord] = []
        self.total_tax_collected: float = 0.0
        self.total_tax_evaded: float = 0.0
        self.total_evasion_fines_collected: float = 0.0

    @classmethod
    def calculate_elastic_truthfulness(cls, taxpayer: NPC, assessor: Optional[NPC], context: Any) -> float:
        p = getattr(taxpayer, "personality", {}) or {}
        sp = getattr(taxpayer, "social_profile", {}) or {}
        v = getattr(taxpayer, "vices", {}) or {}

        c = float(p.get("conscientiousness", 0.5))
        a = float(p.get("agreeableness", 0.5))
        h = float(sp.get("moral_values", {}).get("honor", 0.5))
        crime = float(v.get("crime_propensity", 0.0)) / 100.0

        base_honesty = (c * 0.40) + (h * 0.35) + (a * 0.25)
        criminal_suppression = 1.0 - (crime * 0.85)
        truthfulness = max(0.0, base_honesty * criminal_suppression)

        if assessor:
            op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
            if op_eng and hasattr(op_eng, "get_net_opinion"):
                truthfulness += (op_eng.get_net_opinion(taxpayer.id, assessor.id) / 250.0)

        resentment = float(taxpayer.get_feeling("resentment")) if hasattr(taxpayer, "get_feeling") else 0.0
        if resentment > 30.0:
            truthfulness -= (resentment - 30.0) / 200.0

        return max(0.0, min(1.0, truthfulness))

    def assess_taxpayer(self, taxpayer: NPC, assessor: Optional[NPC], context: Any, current_tick: int) -> Optional[TaxAssessmentRecord]:
        actual_earnings = float(getattr(taxpayer, "_unassessed_earnings_gold", 0.0))
        if actual_earnings <= 0.0:
            return None

        # Institutional Tax Exemption Check (Sacred clergy & exempt vocations)
        occ_l = (getattr(taxpayer, "occupation", "") or "").lower()
        from src.configuration.settings import SettingsRegistry
        civ_cfg = SettingsRegistry.get_instance().get("civic_governance")
        exempt_occs = [k.lower() for k in civ_cfg.get("tax_exemptions", {}).get("exempt_occupations", ["priest", "clergy", "monk", "curate"])]
        if any(k in occ_l for k in exempt_occs):
            taxpayer._unassessed_earnings_gold = 0.0
            return None

        truthfulness = self.calculate_elastic_truthfulness(taxpayer, assessor, context)
        declared = round(actual_earnings * truthfulness, 2)
        tax_due = round(declared * self.tax_rate, 2)
        actual_tax = min(taxpayer.wealth, tax_due)

        taxpayer.wealth = max(0.0, round(taxpayer.wealth - actual_tax, 2))
        treasury = getattr(context, "municipal_treasury", None)
        if treasury and hasattr(treasury, "balance"):
            treasury.balance = round(treasury.balance + actual_tax, 2)

        evaded_tax = max(0.0, round((actual_earnings - declared) * self.tax_rate, 2))
        self.total_tax_collected += actual_tax
        self.total_tax_evaded += evaded_tax

        was_audited = False
        penalty = 0.0
        min_evasion = getattr(self, "audit_evasion_min_threshold", 0.50)
        max_prob = getattr(self, "max_audit_probability", 0.40)
        if evaded_tax > min_evasion:
            audit_chance = min(max_prob, self.audit_vigilance + (evaded_tax / 50.0))
            if context.random.random() < audit_chance:
                was_audited = True
                penalty = round(evaded_tax * self.evasion_penalty_multiplier, 2)
                actual_pen = min(taxpayer.wealth, penalty)
                taxpayer.wealth = max(0.0, round(taxpayer.wealth - actual_pen, 2))
                if treasury and hasattr(treasury, "balance"):
                    treasury.balance = round(treasury.balance + actual_pen, 2)
                self.total_evasion_fines_collected += actual_pen

        taxpayer._unassessed_earnings_gold = 0.0
        rec = TaxAssessmentRecord(
            npc_id=taxpayer.id,
            npc_name=taxpayer.name,
            actual_earnings_gold=actual_earnings,
            declared_earnings_gold=declared,
            tax_rate=self.tax_rate,
            tax_paid_gold=actual_tax,
            evaded_gold=evaded_tax,
            was_audited=was_audited,
            audit_penalty_gold=penalty,
            reporting_truthfulness=truthfulness,
            assessor_id=assessor.id if assessor else None,
            tick=current_tick
        )
        self.assessment_history.append(rec)
        return rec

    def process_settlement_taxes(self, context: Any, current_tick: int) -> List[Dict[str, Any]]:
        assessor = context.find_npc_by_role(["mayor", "magistrate", "notary"])
        assessments = []
        for npc in context.npcs.values():
            if getattr(npc, "current_state", "") == "DECEASED":
                continue
            rec = self.assess_taxpayer(npc, assessor, context, current_tick)
            if rec:
                assessments.append(rec.to_dict())
        return assessments

    def collect_commercial_stall_fees(self, context: Any, current_tick: int) -> float:
        """Collects daily market stall fees from operational commercial premises to replenish the Municipal Treasury."""
        from src.configuration.settings import SettingsRegistry
        gov_cfg = SettingsRegistry.get_instance().get("civic_governance")
        comm_cfg = gov_cfg.get("commercial_taxation", {})
        stall_fee = float(comm_cfg.get("daily_commercial_stall_fee_gold", 0.50))

        treasury = getattr(context, "municipal_treasury", None)
        if not treasury or not hasattr(context, "settlements") or not hasattr(context, "npcs"):
            return 0.0

        total_collected = 0.0
        assessed_owners = set()

        for sett in context.settlements.values():
            for bldg in sett.buildings.values():
                if bldg.category == "COMMERCIAL":
                    owner_id = bldg.owner_id
                    if not owner_id:
                        b_l = (bldg.id + " " + bldg.name).lower()
                        if "tavern" in b_l or "inn" in b_l:
                            prop = context.find_npc_by_role(["innkeeper", "barkeep"]) if hasattr(context, "find_npc_by_role") else None
                            owner_id = prop.id if prop else None
                        elif "bakery" in b_l:
                            prop = context.find_npc_by_role(["baker"]) if hasattr(context, "find_npc_by_role") else None
                            owner_id = prop.id if prop else None
                        elif "shop" in b_l or "emporium" in b_l or "vance" in b_l:
                            prop = context.find_npc_by_role(["merchant", "shopkeeper"]) if hasattr(context, "find_npc_by_role") else None
                            owner_id = prop.id if prop else None

                    if owner_id and owner_id in context.npcs and owner_id not in assessed_owners:
                        assessed_owners.add(owner_id)
                        owner = context.npcs[owner_id]
                        if getattr(owner, "is_alive", True) and getattr(owner, "wealth", 0.0) >= stall_fee:
                            owner.wealth = round(owner.wealth - stall_fee, 2)
                            treasury.balance = round(treasury.balance + stall_fee, 2)
                            self.total_tax_collected += stall_fee
                            total_collected += stall_fee
        return total_collected

    def get_tax_statistics(self) -> Dict[str, Any]:
        return {
            "total_tax_collected_gold": round(self.total_tax_collected, 2),
            "total_tax_evaded_gold": round(self.total_tax_evaded, 2),
            "total_evasion_fines_gold": round(self.total_evasion_fines_collected, 2),
            "total_assessments_count": len(self.assessment_history),
            "audit_rate": round(sum(1 for a in self.assessment_history if a.was_audited) / max(1, len(self.assessment_history)) * 100.0, 1)
        }
