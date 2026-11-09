"""
Fraternal Mutual Aid Lodges & Cooperative Relief Chests.
Operates 100% on declarative configurations from data/settings/fraternal_aid.json.
Models grassroots social security: member dues, emergency sickness/poverty relief,
and spousal bereavement benefits with closed-loop currency conservation.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

@dataclass
class AidLodge:
    lodge_id: str
    name: str
    eligible_occupations: List[str] = field(default_factory=list)
    daily_dues_gold: float = 0.12
    min_wealth_for_dues_gold: float = 12.0
    emergency_poverty_threshold_gold: float = 8.0
    emergency_relief_payout_gold: float = 6.0
    bereavement_benefit_gold: float = 15.0
    min_treasury_reserve_gold: float = 20.0
    treasury_balance: float = 60.0
    member_ids: List[str] = field(default_factory=list)
    relief_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.lodge_id

    def is_npc_eligible(self, npc: Any) -> bool:
        occ = (getattr(npc, "occupation", "") or "").lower()
        if not self.eligible_occupations:
            return True
        return any(k.lower() in occ for k in self.eligible_occupations)


class FraternalAidEngine:
    """
    Central Fraternal Mutual Aid and Sickness Lodge Engine.
    Administers private mutual insurance chests, collects daily dues from solvent members,
    and disburses emergency relief to distressed brethren and grieving spouses.
    """
    _instance: Optional["FraternalAidEngine"] = None

    @classmethod
    def get_instance(cls) -> "FraternalAidEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.lodges: Dict[str, AidLodge] = {}
        self.total_dues_collected_gold: float = 0.0
        self.total_relief_disbursed_gold: float = 0.0
        self.total_relief_cases_count: int = 0
        self.last_dues_tick: int = -9999
        self.relief_history: List[Dict[str, Any]] = []
        self._load_from_settings()

    def clear(self) -> None:
        self.total_dues_collected_gold = 0.0
        self.total_relief_disbursed_gold = 0.0
        self.total_relief_cases_count = 0
        self.last_dues_tick = -9999
        self.relief_history.clear()
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        cfg = SettingsRegistry.get_instance().get("fraternal_aid")
        lodge_defs = cfg.get("aid_lodges", {})
        self.lodges.clear()

        for l_id, data in lodge_defs.items():
            self.lodges[l_id] = AidLodge(
                lodge_id=l_id,
                name=data.get("name", "Mutual Aid Lodge"),
                eligible_occupations=list(data.get("eligible_occupations", [])),
                daily_dues_gold=float(data.get("daily_dues_gold", 0.12)),
                min_wealth_for_dues_gold=float(data.get("min_wealth_for_dues_gold", 12.0)),
                emergency_poverty_threshold_gold=float(data.get("emergency_poverty_threshold_gold", 8.0)),
                emergency_relief_payout_gold=float(data.get("emergency_relief_payout_gold", 6.0)),
                bereavement_benefit_gold=float(data.get("bereavement_benefit_gold", 15.0)),
                min_treasury_reserve_gold=float(data.get("min_treasury_reserve_gold", 20.0)),
                treasury_balance=float(data.get("initial_treasury_balance", 60.0))
            )

    def auto_discover_members(self, context: Any) -> None:
        """Discovers settlement NPCs and registers them into eligible fraternal lodges."""
        if not hasattr(context, "npcs") or not context.npcs:
            return
        if not self.lodges:
            self._load_from_settings()

        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            for lodge in self.lodges.values():
                if lodge.is_npc_eligible(npc) and npc.id not in lodge.member_ids:
                    lodge.member_ids.append(npc.id)

    def collect_daily_dues(self, context: Any, current_tick: int) -> float:
        """
        Collects daily dues from solvent members, depositing into lodge chests.
        Members below the solvency buffer are exempted.
        """
        if current_tick - self.last_dues_tick < 1440:
            return 0.0

        self.last_dues_tick = current_tick
        total_collected = 0.0

        for lodge in self.lodges.values():
            for m_id in lodge.member_ids:
                member = context.npcs.get(m_id) if hasattr(context, "npcs") else None
                if not member or not getattr(member, "is_alive", True):
                    continue
                if float(getattr(member, "wealth", 0.0)) >= lodge.min_wealth_for_dues_gold:
                    # Dynamic dues scaling: if chest reserve is low, scale dues slightly up to replenish chest
                    due = lodge.daily_dues_gold
                    if lodge.treasury_balance < (lodge.min_treasury_reserve_gold * 1.5):
                        due = round(lodge.daily_dues_gold * 1.4, 2)
                    member.wealth = round(member.wealth - due, 2)
                    lodge.treasury_balance = round(lodge.treasury_balance + due, 2)
                    total_collected += due
                    self.total_dues_collected_gold += due

        return round(total_collected, 2)

    def evaluate_emergency_relief(self, context: Any, current_tick: int) -> List[Dict[str, Any]]:
        """
        Evaluates distressed members in poverty or severe somatic crisis.
        Disburses mutual aid payouts directly from lodge reserves.
        """
        relief_granted = []
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        for lodge in self.lodges.values():
            if lodge.treasury_balance <= lodge.min_treasury_reserve_gold:
                continue

            for m_id in lodge.member_ids:
                member = context.npcs.get(m_id) if hasattr(context, "npcs") else None
                if not member or not getattr(member, "is_alive", True):
                    continue

                w = float(getattr(member, "wealth", 0.0))
                energy = float(getattr(member, "needs", {}).get("energy", 100.0))
                stress = float(getattr(member, "feelings", {}).get("stress", 0.0))

                # Distress condition: poverty or somatic collapse
                is_distressed = (w < lodge.emergency_poverty_threshold_gold) or (energy < 15.0 and stress > 60.0)
                available_funds = lodge.treasury_balance - lodge.min_treasury_reserve_gold

                if is_distressed and available_funds >= lodge.emergency_relief_payout_gold:
                    payout = lodge.emergency_relief_payout_gold
                    lodge.treasury_balance = round(lodge.treasury_balance - payout, 2)
                    member.wealth = round(member.wealth + payout, 2)
                    member.adjust_feeling("contentment", 18.0)
                    member.adjust_feeling("stress", -20.0)

                    case = {
                        "lodge_id": lodge.lodge_id,
                        "lodge_name": lodge.name,
                        "recipient_id": member.id,
                        "recipient_name": member.name,
                        "payout_gold": payout,
                        "tick": current_tick
                    }
                    lodge.relief_history.append(case)
                    relief_granted.append(case)
                    self.total_relief_disbursed_gold += payout
                    self.total_relief_cases_count += 1

                    member.record_biographical_entry(
                        current_tick, time_iso, "FRATERNAL_AID_RECEIVED",
                        f"Received {payout:.1f}g emergency sickness & calamity benefit from {lodge.name}."
                    )
                    break # One relief case per lodge per evaluation pass to protect reserves

        return relief_granted

    def disburse_bereavement_benefit(
        self,
        deceased_npc: Any,
        surviving_spouse: Any,
        context: Any,
        current_tick: int
    ) -> Optional[Dict[str, Any]]:
        """
        Disburses lodge bereavement benefits to the surviving spouse upon a member's demise.
        """
        if not surviving_spouse or not getattr(surviving_spouse, "is_alive", True):
            return None

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        for lodge in self.lodges.values():
            if deceased_npc.id in lodge.member_ids:
                avail = lodge.treasury_balance - lodge.min_treasury_reserve_gold
                if avail >= 10.0:
                    payout = min(lodge.bereavement_benefit_gold, avail)
                    lodge.treasury_balance = round(lodge.treasury_balance - payout, 2)
                    surviving_spouse.wealth = round(surviving_spouse.wealth + payout, 2)
                    surviving_spouse.adjust_feeling("grief", -15.0) # Comfort in sorrow

                    case = {
                        "lodge_id": lodge.lodge_id,
                        "deceased_name": deceased_npc.name,
                        "spouse_name": surviving_spouse.name,
                        "payout_gold": payout,
                        "tick": current_tick
                    }
                    lodge.relief_history.append(case)
                    self.total_relief_disbursed_gold += payout
                    surviving_spouse.record_biographical_entry(
                        current_tick, time_iso, "BEREAVEMENT_AID_RECEIVED",
                        f"Received {payout:.1f}g fraternal bereavement benefit from {lodge.name} following the demise of {deceased_npc.name}."
                    )
                    return case

        return None
