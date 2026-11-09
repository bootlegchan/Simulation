"""
Municipal Decrees, Town Council Legislation, and Ordinance Enforcement.
Operates 100% on declarative policies from data/settings/decrees.json.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

class DecreeType(str, Enum):
    NOCTURNAL_CURFEW = "NOCTURNAL_CURFEW"
    BREAD_PRICE_CEILING = "BREAD_PRICE_CEILING"
    SUMPTUARY_SPENDING_CAP = "SUMPTUARY_SPENDING_CAP"
    INFRASTRUCTURE_REPAIR_MANDATE = "INFRASTRUCTURE_REPAIR_MANDATE"

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
class ActiveDecreeRecord:
    decree_id: str
    name: str
    description: str
    enacted_tick: int
    expires_tick: int
    effects: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decree_id": self.decree_id,
            "name": self.name,
            "description": self.description,
            "enacted_tick": self.enacted_tick,
            "expires_tick": self.expires_tick,
            "effects": self.effects
        }

class MunicipalDecreeEngine:
    """
    Central Municipal Decree & Town Council Legislative Engine.
    Handles council voting, ordinance enactment, expiry tracking, and civic behavioral mandates.
    """
    _instance: Optional["MunicipalDecreeEngine"] = None

    @classmethod
    def get_instance(cls) -> "MunicipalDecreeEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.active_decrees: Dict[str, ActiveDecreeRecord] = {}
        self.decree_history: List[ActiveDecreeRecord] = []
        self.total_decrees_enacted: int = 0
        self.total_decrees_repealed: int = 0

    def get_decrees_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("decrees").get("decrees", {})

    def is_decree_active(self, decree_id: str) -> bool:
        return decree_id in self.active_decrees

    def get_active_decree_modifiers(self) -> Dict[str, Any]:
        combined: Dict[str, Any] = {}
        for d in self.active_decrees.values():
            combined.update(d.effects)
        return combined

    def enact_decree(
        self,
        decree_id: str,
        context: Any,
        tick: int,
        custom_duration: Optional[int] = None
    ) -> Optional[ActiveDecreeRecord]:
        """Formally passes and enacts a municipal decree."""
        cfg = self.get_decrees_config()
        if decree_id not in cfg:
            return None

        spec = cfg[decree_id]
        dur = custom_duration or int(spec.get("duration_ticks", 7200))

        record = ActiveDecreeRecord(
            decree_id=decree_id,
            name=spec.get("name", decree_id),
            description=spec.get("description", "Municipal ordinance"),
            enacted_tick=tick,
            expires_tick=tick + dur,
            effects=dict(spec.get("effects", {}))
        )
        self.active_decrees[decree_id] = record
        self.total_decrees_enacted += 1

        # Publish notice to CIVIC_NOTICES
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
        public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
        if info_eng:
            info_eng.publish_item(
                channel="CIVIC_NOTICES",
                topic=f"DECREE_ENACTED_{decree_id}",
                headline=f"Municipal Ordinance Enacted: {record.name}",
                content=f"{record.description} (Duration: {dur // 1440} days).",
                target_location_id=public_plaza,
                payload={"decree_id": decree_id, "effects": record.effects},
                current_tick=tick,
                custom_duration=dur
            )

        # Epistemic Legislative Fact Atom: Pinned to physical room notice boards
        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng:
                from src.society.epistemic_engine import EpistemicStatus, VisibilityTier, CarrierType
                dec_atom = ep_eng.create_atom(
                    title=f"Municipal Decree: {record.name}",
                    content=record.description,
                    status=EpistemicStatus.FACT,
                    visibility=VisibilityTier.PUBLIC_SETTLEMENT,
                    carrier_type=CarrierType.NOTE,
                    location_id=public_plaza,
                    emotional_relevance=1.4,
                    created_tick=tick,
                    tags=["decree", decree_id.lower(), "law", "ordinance"],
                    associative_keys=[decree_id.lower(), "decree", "law", "ordinance"],
                    payload={"decree_id": decree_id, "effects": record.effects}
                )
                ep_eng.post_to_notice_board(public_plaza, dec_atom)
                ep_eng.post_to_notice_board("room_town_hall", dec_atom)

        return record

    def repeal_decree(self, decree_id: str, context: Optional[Any] = None, tick: int = 0) -> bool:
        """Repeals or expires an active decree."""
        if decree_id in self.active_decrees:
            rec = self.active_decrees.pop(decree_id)
            self.decree_history.append(rec)
            self.total_decrees_repealed += 1

            if context:
                info_eng = context.get_service("unified_information_engine")
                if info_eng:
                    public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
                    info_eng.publish_item(
                        channel="CIVIC_NOTICES",
                        topic=f"DECREE_REPEALED_{decree_id}",
                        headline=f"Municipal Decree Concluded: {rec.name}",
                        content=f"The mandate for {rec.name} has concluded and is no longer enforced.",
                        target_location_id=public_plaza,
                        current_tick=tick,
                        custom_duration=4320
                    )
            return True
        return False

    def convene_town_council(self, context: Any, tick: int) -> List[Dict[str, Any]]:
        """
        Assembles Town Council delegates to deliberate on municipal decrees:
        Council consists of: Mayor, Priest, Guildmaster, and Agrarian delegate.
        Votes are cast based on faction platforms and member grievances.
        """
        enacted_records = []
        fact_eng = context.get_service("faction_political_engine")
        if not fact_eng or not hasattr(fact_eng, "factions"):
            return []

        decree_catalog = self.get_decrees_config()
        for d_id, d_spec in decree_catalog.items():
            if self.is_decree_active(d_id):
                continue

            min_vote_ratio = float(d_spec.get("minimum_council_vote", 0.50))
            favorable_votes = 0.0
            total_voting_weight = 0.0

            for faction in fact_eng.factions.values():
                weight = faction.base_influence / 30.0
                total_voting_weight += weight

                if d_id in faction.favored_decrees:
                    favorable_votes += weight
                elif d_id in faction.opposed_decrees:
                    favorable_votes += 0.0
                else:
                    favorable_votes += (weight * 0.50)  # Neutral stance

            ratio = favorable_votes / max(1.0, total_voting_weight)
            if ratio >= min_vote_ratio:
                rec = self.enact_decree(d_id, context, tick)
                if rec:
                    enacted_records.append({"decree_id": d_id, "vote_ratio": round(ratio, 2), "name": rec.name})

        return enacted_records

    def process_daily_decree_cycles(self, npcs: Any, tick: int, context: Optional[Any] = None) -> List[str]:
        """Daily maintenance cycle: expires outdated decrees."""
        expired = []
        for d_id in list(self.active_decrees.keys()):
            rec = self.active_decrees[d_id]
            if tick >= rec.expires_tick:
                self.repeal_decree(d_id, context, tick)
                expired.append(d_id)
        return expired

    def knows_decree(self, npc: Any, decree_id: str, context: Optional[Any] = None) -> bool:
        """Subjective Epistemic Check: Returns whether an NPC personally knows about this municipal decree."""
        if not self.is_decree_active(decree_id):
            return False
        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng:
                traces = ep_eng.npc_memories.get(npc.id, {})
                for trace in traces.values():
                    if trace.atom.payload.get("decree_id") == decree_id or decree_id.lower() in trace.atom.tags:
                        if not trace.is_dormant(threshold=0.08):
                            return True

            info_eng = context.get_service("unified_information_engine")
            if info_eng and hasattr(info_eng, "npc_knowledge_ledger"):
                known_set = info_eng.npc_knowledge_ledger.get(npc.id, set())
                for item_id in known_set:
                    item = info_eng.active_items.get(item_id)
                    if item and item.payload.get("decree_id") == decree_id:
                        return True

        # Officials and civic authorities always know municipal laws
        occ = (getattr(npc, "occupation", "") or "").lower()
        if any(k in occ for k in ("mayor", "magistrate", "notary", "clerk", "guard")):
            return True

        return False

