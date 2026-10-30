"""
Social Information Channels and Epistemic Learning Engines.
Enables NPCs to learn about the world through diverse communication contexts:
1. Public Notice Boards & Bulletins (NoticeBoardEngine)
2. Workplace Professional Chatter (WorkplaceChatterEngine)
3. Tavern & Public Social Gatherings (TavernSocialGatheringEngine)
4. Cross-Channel Epistemic Belief Synthesis & Reinforcement (EpistemicBeliefEngine)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import uuid

from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.npc.memory import MemorySystem, MemoryEntry, SemanticBelief

@dataclass
class NoticeBulletin:
    bulletin_id: str
    board_id: str
    topic_category: str  # "CIVIC_ANNOUNCEMENT", "CRIMINAL_WARRANT", "JOB_OFFERING", "COMMODITY_SCARCITY"
    title: str
    content_payload: Dict[str, Any]
    posted_by_id: str
    posted_tick: int
    importance_score: float = 50.0

class NoticeBoardEngine:
    """Manages public notice boards, bulletin postings, and NPC reading/learning mechanics."""

    def __init__(self):
        self.bulletins: Dict[str, List[NoticeBulletin]] = {}  # board_id -> List[NoticeBulletin]

    def post_bulletin(
        self,
        board_id: str,
        topic_category: str,
        title: str,
        content_payload: Dict[str, Any],
        posted_by_id: str,
        posted_tick: int,
        importance_score: float = 50.0
    ) -> NoticeBulletin:
        bulletin_id = f"bulletin_{uuid.uuid4().hex[:8]}"
        bulletin = NoticeBulletin(
            bulletin_id=bulletin_id,
            board_id=board_id,
            topic_category=topic_category,
            title=title,
            content_payload=content_payload,
            posted_by_id=posted_by_id,
            posted_tick=posted_tick,
            importance_score=importance_score
        )
        if board_id not in self.bulletins:
            self.bulletins[board_id] = []
        self.bulletins[board_id].append(bulletin)
        return bulletin

    def read_notice_board(
        self,
        npc: NPC,
        notice_board_obj: InteractiveObject,
        memory_system: MemorySystem,
        current_tick: int
    ) -> Dict[str, Any]:
        board_id = notice_board_obj.id
        posted_notices = self.bulletins.get(board_id, [])

        unread_count = 0
        learned_bulletins = []

        for notice in posted_notices:
            fact_key = f"notice:{notice.topic_category}:{notice.bulletin_id}"
            
            # Check if NPC already knows this notice
            if fact_key not in memory_system.semantic_beliefs:
                unread_count += 1
                
                # Add Semantic Belief
                memory_system.update_semantic_belief(
                    fact_key=fact_key,
                    knowledge_payload=notice.content_payload,
                    confidence_score=1.0,  # Public notice board carries 100% objective credibility
                    source_attribution=f"notice_board:{board_id}",
                    current_tick=current_tick
                )

                # Record Episodic Memory
                memory_system.record(
                    memory_id=f"mem_read_{notice.bulletin_id}_{npc.id}",
                    event_type=f"notice_read_{notice.topic_category.lower()}",
                    subject_id=notice.posted_by_id,
                    tick=current_tick,
                    payload={"notice_id": notice.bulletin_id, "title": notice.title, "payload": notice.content_payload},
                    salience=notice.importance_score / 10.0
                )

                learned_bulletins.append(notice.title)

                # Behavioral Need & Desire Impacts
                if notice.topic_category == "JOB_OFFERING":
                    if npc.wealth < 30.0 or npc.occupation == "Unemployed":
                        npc.needs["ambition"] = min(100.0, npc.needs.get("ambition", 50.0) + 20.0)
                elif notice.topic_category == "CRIMINAL_WARRANT":
                    suspect_id = notice.content_payload.get("suspect_id")
                    if suspect_id == npc.id:
                        # Suspect reads their own warrant -> High Stress!
                        npc.needs["stress"] = min(100.0, npc.needs.get("stress", 50.0) + 30.0)
                    else:
                        # Citizen reads warrant -> Vigilance boost
                        npc.needs["vigilance"] = min(100.0, npc.needs.get("vigilance", 50.0) + 15.0)
                elif notice.topic_category == "COMMODITY_SCARCITY":
                    # Inflation warning -> Economic anxiety
                    npc.needs["economic_anxiety"] = min(100.0, npc.needs.get("economic_anxiety", 20.0) + 25.0)

        # Satisfy Curiosity & Moderate Social Need
        if unread_count > 0:
            npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + 15.0)
            npc.needs["curiosity"] = max(0.0, npc.needs.get("curiosity", 50.0) - 30.0)

        return {
            "npc_id": npc.id,
            "board_id": board_id,
            "unread_count": unread_count,
            "learned_bulletins": learned_bulletins
        }


class WorkplaceChatterEngine:
    """Manages professional interactions between co-located working NPCs."""

    @staticmethod
    def process_workplace_chatter(
        workers: List[NPC],
        work_location_id: str,
        memory_systems: Dict[str, MemorySystem],
        current_tick: int
    ) -> Dict[str, Any]:
        if len(workers) < 2:
            return {"chatter_occurred": False, "reason": "Insufficient co-located workers"}

        exchanges = []
        for i in range(len(workers)):
            for j in range(i + 1, len(workers)):
                w1 = workers[i]
                w2 = workers[j]
                m1 = memory_systems.get(w1.id)
                m2 = memory_systems.get(w2.id)

                if not m1 or not m2:
                    continue

                # Formulate professional topic based on occupation
                topic = f"trade_technique:{w1.occupation.lower()}"
                fact_key = f"workplace_fact:{topic}"

                # Worker 1 shares knowledge with Worker 2
                payload = {
                    "occupation": w1.occupation,
                    "location_id": work_location_id,
                    "tip": f"Efficiency tip for {w1.occupation} work at {work_location_id}"
                }

                m2.update_semantic_belief(
                    fact_key=fact_key,
                    knowledge_payload=payload,
                    confidence_score=0.85,  # Workplace professional talk carries 85% credibility
                    source_attribution=f"workplace_chatter:{w1.id}",
                    current_tick=current_tick
                )

                m1.update_semantic_belief(
                    fact_key=fact_key,
                    knowledge_payload=payload,
                    confidence_score=0.85,
                    source_attribution=f"workplace_chatter:{w2.id}",
                    current_tick=current_tick
                )

                # Need Satisfaction & Camaraderie
                w1.needs["social"] = min(100.0, w1.needs.get("social", 50.0) + 15.0)
                w2.needs["social"] = min(100.0, w2.needs.get("social", 50.0) + 15.0)
                w1.needs["stress"] = max(0.0, w1.needs.get("stress", 50.0) - 10.0)
                w2.needs["stress"] = max(0.0, w2.needs.get("stress", 50.0) - 10.0)

                exchanges.append((w1.id, w2.id, topic))

        return {
            "chatter_occurred": True,
            "work_location_id": work_location_id,
            "exchanges_count": len(exchanges),
            "exchanges": exchanges
        }


class TavernSocialGatheringEngine:
    """Manages informal, organic social encounters in taverns, bars, and public squares."""

    @staticmethod
    def process_tavern_gathering(
        patrons: List[NPC],
        location_id: str,
        memory_systems: Dict[str, MemorySystem],
        social_network: Any,
        current_tick: int,
        random_gen: Any
    ) -> Dict[str, Any]:
        if len(patrons) < 2:
            return {"gathering_occurred": False, "reason": "Insufficient patrons"}

        outcomes = []
        for i in range(len(patrons)):
            for j in range(i + 1, len(patrons)):
                p1 = patrons[i]
                p2 = patrons[j]
                m1 = memory_systems.get(p1.id)
                m2 = memory_systems.get(p2.id)

                if not m1 or not m2:
                    continue

                # Determine interaction type based on random roll and personality
                roll = random_gen.random() if hasattr(random_gen, "random") else 0.5

                if roll < 0.4:
                    # Type 1: Rumor & Scandal Gossip
                    scandal_fact = f"scandal_gossip:tavern_{location_id}"
                    payload = {
                        "topic": "Scandalous Town Gossip",
                        "claim": f"{p1.name} and {p2.name} discussed town secrets at {location_id}"
                    }
                    trust_score = social_network.get_relationship(p2.id, p1.id) if hasattr(social_network, "get_relationship") else 50.0
                    credibility = max(0.4, min(0.9, 0.5 + (trust_score / 200.0)))

                    m2.update_semantic_belief(
                        fact_key=scandal_fact,
                        knowledge_payload=payload,
                        confidence_score=round(credibility, 2),
                        source_attribution=f"tavern_gossip:{p1.id}",
                        current_tick=current_tick
                    )

                    outcomes.append(f"Gossip shared between {p1.name} and {p2.name}")

                elif roll < 0.7:
                    # Type 2: Flirtation & Romantic Bonding
                    p1.needs["romance_drive"] = min(100.0, p1.needs.get("romance_drive", 20.0) + 20.0)
                    p2.needs["romance_drive"] = min(100.0, p2.needs.get("romance_drive", 20.0) + 20.0)
                    outcomes.append(f"Flirtation exchanged between {p1.name} and {p2.name}")

                else:
                    # Type 3: Political & Faction Debate
                    p1.needs["political_engagement"] = min(100.0, p1.needs.get("political_engagement", 20.0) + 15.0)
                    p2.needs["political_engagement"] = min(100.0, p2.needs.get("political_engagement", 20.0) + 15.0)
                    outcomes.append(f"Political debate between {p1.name} and {p2.name}")

                # High Need Satisfaction for Leisure Venues
                p1.needs["social"] = min(100.0, p1.needs.get("social", 50.0) + 35.0)
                p2.needs["social"] = min(100.0, p2.needs.get("social", 50.0) + 35.0)
                p1.needs["energy"] = max(0.0, p1.needs.get("energy", 50.0) - 5.0)  # Moderate exertion
                p2.needs["energy"] = max(0.0, p2.needs.get("energy", 50.0) - 5.0)
                p1.needs["stress"] = max(0.0, p1.needs.get("stress", 50.0) - 25.0)
                p2.needs["stress"] = max(0.0, p2.needs.get("stress", 50.0) - 25.0)

        return {
            "gathering_occurred": True,
            "location_id": location_id,
            "patrons_count": len(patrons),
            "outcomes": outcomes
        }


class EpistemicBeliefEngine:
    """Cross-channel information synthesis and belief reinforcement engine."""

    @staticmethod
    def synthesize_and_reinforce_beliefs(npc: NPC, memory_system: MemorySystem) -> Dict[str, Any]:
        """
        Scans semantic beliefs. When the same underlying topic is confirmed across multiple distinct
        source attributions (e.g. notice board + workplace + tavern), reinforces confidence and retention.
        """
        attributions_by_topic: Dict[str, Set[str]] = {}

        for fact_key, belief in memory_system.semantic_beliefs.items():
            topic_prefix = fact_key.split(":")[0] if ":" in fact_key else fact_key
            if topic_prefix not in attributions_by_topic:
                attributions_by_topic[topic_prefix] = set()
            attributions_by_topic[topic_prefix].add(belief.source_attribution)

        reinforced_topics = []

        for topic_prefix, sources in attributions_by_topic.items():
            if len(sources) >= 2:
                # Multi-source confirmation! Boost confidence to 100% and reduce anxiety
                for fact_key, belief in memory_system.semantic_beliefs.items():
                    if fact_key.startswith(topic_prefix):
                        belief.confidence_score = 1.0
                
                reinforced_topics.append(topic_prefix)

                # Behavioral Impact: Firm conviction increases goal motivation
                npc.needs["conviction"] = min(100.0, npc.needs.get("conviction", 50.0) + 20.0)

        return {
            "npc_id": npc.id,
            "reinforced_topics_count": len(reinforced_topics),
            "reinforced_topics": reinforced_topics
        }
