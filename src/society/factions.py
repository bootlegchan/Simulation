"""
Political Factions, Guild Agendas, Continuous Grievances, and Labor Strikes.
Operates 100% on declarative platforms from data/settings/factions.json.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

@dataclass
class Faction:
    faction_id: str
    name: str
    agenda: str = "POPULAR_WELFARE"
    leader_id: Optional[str] = None
    leader_role: Optional[str] = None
    member_ids: List[str] = field(default_factory=list)
    eligible_occupations: List[str] = field(default_factory=list)
    favored_decrees: List[str] = field(default_factory=list)
    opposed_decrees: List[str] = field(default_factory=list)
    strike_threshold: float = 70.0
    base_influence: float = 35.0
    current_grievance: float = 0.0
    is_on_strike: bool = False
    strike_started_tick: int = 0
    platform_priorities: Optional[Any] = None
    eligible_classes: Optional[Any] = None
    min_crime_propensity: float = 0.0

    @property
    def id(self) -> str:
        return self.faction_id

    def is_npc_eligible(self, npc: Any) -> bool:
        """Determines if an NPC meets recruitment eligibility for this faction."""
        occ = (getattr(npc, "occupation", "") or "").lower()
        if not self.eligible_occupations:
            return True
        return any(k.lower() in occ for k in self.eligible_occupations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "name": self.name,
            "agenda": self.agenda,
            "leader_id": self.leader_id,
            "member_count": len(self.member_ids),
            "current_grievance": round(self.current_grievance, 2),
            "is_on_strike": self.is_on_strike,
            "strike_started_tick": self.strike_started_tick,
            "base_influence": self.base_influence
        }

class FactionPoliticalEngine:
    """
    Central Faction Political & Labor Agitation Engine.
    Tracks member grievances, evaluates labor strikes, and coordinates faction influence.
    """
    _instance: Optional["FactionPoliticalEngine"] = None

    @classmethod
    def get_instance(cls) -> "FactionPoliticalEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.factions: Dict[str, Faction] = {}
        self.total_strikes_declared: int = 0
        self.total_strikes_resolved: int = 0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        f_cfg = SettingsRegistry.get_instance().get("factions")
        factions_data = f_cfg.get("factions", {})
        for f_id, data in factions_data.items():
            self.factions[f_id] = Faction(
                faction_id=f_id,
                name=data.get("name", "Faction"),
                agenda=data.get("agenda", "GENERAL_WELFARE"),
                leader_role=data.get("leader_role"),
                eligible_occupations=list(data.get("eligible_occupations", [])),
                favored_decrees=list(data.get("favored_decrees", [])),
                opposed_decrees=list(data.get("opposed_decrees", [])),
                strike_threshold=float(data.get("strike_threshold", 70.0)),
                base_influence=float(data.get("base_influence", 30.0))
            )

    def auto_discover_members(self, context: Any) -> None:
        """Discovers settlement NPCs and registers them into eligible factions."""
        if not hasattr(context, "npcs") or not context.npcs:
            return
        if not self.factions:
            self._load_from_settings()

        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            for faction in self.factions.values():
                if faction.is_npc_eligible(npc) and npc.id not in faction.member_ids:
                    faction.member_ids.append(npc.id)
                    # Assign leader if matching leader role
                    if not faction.leader_id and faction.leader_role:
                        if faction.leader_role in (npc.occupation or "").lower():
                            faction.leader_id = npc.id

    def calculate_faction_grievance(self, faction: Faction, context: Any) -> float:
        """
        Calculates continuous faction grievance from member well-being and active decrees:
        G = (1/|M|) * sum(Resentment + (100 - Contentment)*0.4 + Poverty*0.3) + DecreeTension
        """
        if not faction.member_ids or not hasattr(context, "npcs"):
            return 0.0

        total_member_grievance = 0.0
        member_count = 0

        for m_id in faction.member_ids:
            member = context.npcs.get(m_id)
            if not member or not getattr(member, "is_alive", True):
                continue
            resentment = float(member.feelings.get("resentment", 0.0))
            contentment = float(member.feelings.get("contentment", 50.0))
            wealth = float(getattr(member, "wealth", 50.0))
            poverty_strain = max(0.0, 30.0 - wealth)

            member_g = resentment + ((100.0 - contentment) * 0.40) + (poverty_strain * 0.50)
            total_member_grievance += member_g
            member_count += 1

        base_g = (total_member_grievance / max(1, member_count)) if member_count > 0 else 0.0

        # Opposed decree tension
        decree_eng = context.get_service("municipal_decree_engine")
        decree_tension = 0.0
        if decree_eng and hasattr(decree_eng, "active_decrees"):
            for d_id in decree_eng.active_decrees:
                if d_id in faction.opposed_decrees:
                    decree_tension += 15.0

        final_grievance = round(base_g + decree_tension, 2)
        faction.current_grievance = final_grievance
        return final_grievance

    def evaluate_daily_faction_agitation(
        self,
        factions: Dict[str, Faction],
        npcs: Dict[str, Any],
        context: Any,
        tick: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluates daily faction grievances and triggers/resolves labor strikes.
        """
        self.auto_discover_members(context)
        strike_events = []
        info_eng = context.get_service("unified_information_engine")
        public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"

        for faction in (factions or self.factions).values():
            grievance = self.calculate_faction_grievance(faction, context)

            # 1. Strike Trigger (Grievance exceeds strike threshold)
            if grievance >= faction.strike_threshold and not faction.is_on_strike:
                faction.is_on_strike = True
                faction.strike_started_tick = tick
                self.total_strikes_declared += 1

                event_desc = f"{faction.name} declared a general labor strike over economic and regulatory grievances (grievance: {grievance:.1f})."
                strike_events.append({"action": "STRIKE_DECLARED", "faction_id": faction.id, "grievance": grievance})

                if info_eng:
                    info_eng.publish_item(
                        channel="CIVIC_NOTICES",
                        topic="LABOR_STRIKE_DECLARED",
                        headline=f"Municipal Crisis: {faction.name} Enters Labor Strike",
                        content=event_desc,
                        target_location_id=public_plaza,
                        current_tick=tick,
                        custom_duration=7200
                    )

            # 2. Strike Resolution (Grievance drops below threshold buffer)
            elif faction.is_on_strike and grievance < (faction.strike_threshold - 10.0):
                faction.is_on_strike = False
                self.total_strikes_resolved += 1

                event_desc = f"{faction.name} resolved its labor strike as member contentment recovered (grievance: {grievance:.1f})."
                strike_events.append({"action": "STRIKE_RESOLVED", "faction_id": faction.id, "grievance": grievance})

                if info_eng:
                    info_eng.publish_item(
                        channel="CIVIC_NOTICES",
                        topic="LABOR_STRIKE_RESOLVED",
                        headline=f"Civic Notice: {faction.name} Resumes Labor Operations",
                        content=event_desc,
                        target_location_id=public_plaza,
                        current_tick=tick,
                        custom_duration=4320
                    )

        return strike_events

    def process_daily_grievance_decay(self, factions: Dict[str, Faction]) -> None:
        """Applies passive daily relaxation of political grievance."""
        for faction in (factions or self.factions).values():
            if faction.current_grievance > 0.0:
                faction.current_grievance = max(0.0, round(faction.current_grievance - 0.50, 2))

    def is_member_on_strike(self, npc: Any) -> bool:
        """Returns True if the citizen belongs to an active striking faction."""
        for faction in self.factions.values():
            if faction.is_on_strike and npc.id in faction.member_ids:
                return True
        return False
