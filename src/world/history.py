"""
Historical Settlement Background Generator.
Generates an initial 10-20 year history log prior to Tick 1 start, pre-seeding initial memories,
acquaintances, trust scores, and secret ties into NPC Memory Systems.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.core.randomness import SeededRandom
from src.entities.npc import NPC
from src.npc.memory import MemorySystem
from src.society.relationships import SocialNetwork

@dataclass
class HistoricalEvent:
    event_id: str
    year_offset: int  # e.g. -5 means 5 years ago
    title: str
    description: str
    involved_npc_ids: List[str] = None

class SettlementHistoryGenerator:
    """Pre-generates historical backstory events and seeds memories/relationships before Tick 1."""

    @staticmethod
    def generate_town_history(
        settlement_name: str,
        npcs: Dict[str, NPC],
        social_network: SocialNetwork,
        random_gen: SeededRandom,
        history_years: int = 15
    ) -> List[HistoricalEvent]:
        events = []
        npc_ids = list(npcs.keys())

        if len(npc_ids) < 2:
            return events

        # 1. Town Founding Event
        events.append(
            HistoricalEvent(
                event_id="hist_founding",
                year_offset=-history_years,
                title=f"Founding of {settlement_name}",
                description=f"The settlement of {settlement_name} was formally chartered by pioneer families.",
                involved_npc_ids=npc_ids[:4]
            )
        )

        # 2. Historical Bumper Harvest / Famine
        events.append(
            HistoricalEvent(
                event_id="hist_bumper_harvest",
                year_offset=-8,
                title="The Great Bumper Harvest",
                description="A golden autumn yield brought prosperity and strengthened trade ties.",
                involved_npc_ids=npc_ids[::2]
            )
        )

        # 3. Interpersonal Feud / Secret Trade Deal
        if len(npc_ids) >= 3:
            npc_a = npcs[npc_ids[0]]
            npc_b = npcs[npc_ids[1]]
            events.append(
                HistoricalEvent(
                    event_id="hist_blackmarket_feud",
                    year_offset=-3,
                    title="The Grain Smuggling Dispute",
                    description=f"{npc_a.name} accused {npc_b.name} of illicit grain price manipulation.",
                    involved_npc_ids=[npc_a.id, npc_b.id]
                )
            )

            # Pre-seed trust and secret memory in memory system
            social_network.set_relationship(npc_a.id, npc_b.id, -45.0)

            for npc in [npc_a, npc_b]:
                mem_sys = getattr(npc, "memory_system", None)
                if mem_sys is None:
                    mem_sys = MemorySystem()
                    npc.memory_system = mem_sys

                mem_sys.record(
                    memory_id=f"mem_hist_feud_{npc.id}",
                    event_type="historical_feud",
                    subject_id=npc_b.id if npc.id == npc_a.id else npc_a.id,
                    tick=-4320,  # 3 years ago in ticks
                    payload={"event": "The Grain Smuggling Dispute", "animosity": 45.0},
                    salience=8.0
                )

        return events
