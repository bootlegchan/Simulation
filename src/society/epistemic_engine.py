"""
Unified Epistemic Engine: Knowledge Atoms, Inscribed Physical Carriers, Associative Memory Priming,
Crime Investigations, Dyadic Conversation Threads, and Relational Attention Budgets.
Operates 100% on declarative configurations from data/settings/epistemic_system.json.
Models information as first-class multi-axial reality (Epistemic Status x Visibility Tier x Carrier).
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from src.configuration.settings import SettingsRegistry


class EpistemicStatus(str, Enum):
    FACT = "FACT"                               # Directly observed reality or verified accounting
    PRESUMPTION = "PRESUMPTION"                 # High-confidence deductive inference from evidence
    ASSUMPTION = "ASSUMPTION"                   # Heuristic cultural default or unverified prior
    GUESS = "GUESS"                             # Speculative hearsay, conjecture, or rumor
    INTERNAL_THOUGHT = "INTERNAL_THOUGHT"       # Inner subjective reflection, doubt, or suspicion
    TUTORIAL_EXPLANATION = "TUTORIAL_EXPLANATION" # Pedagogical skill instruction or trade manual

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None


class VisibilityTier(str, Enum):
    INTERNAL_MIND = "INTERNAL_MIND"             # Inner thought known only to the self
    SECRET = "SECRET"                           # Clandestine knowledge under oath or criminal liability
    CONFIDENTIAL = "CONFIDENTIAL"               # Restricted institutional/council/guild records
    PRIVATE_DYADIC = "PRIVATE_DYADIC"           # Shared bilateral interpersonal confidence
    PUBLIC_SETTLEMENT = "PUBLIC_SETTLEMENT"     # Open town bulletin, notice board, or plaza talk

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None


class CarrierType(str, Enum):
    MIND = "MIND"                               # Brain trace in biological memory
    BOOK = "BOOK"                               # Inscribed tome or trade manual
    LEDGER = "LEDGER"                           # Administrative accounting ledger
    LETTER = "LETTER"                           # Wax-sealed correspondence
    NOTE = "NOTE"                               # Cryptic slip or chalk cipher
    PHYSICAL_CLUE = "PHYSICAL_CLUE"             # Physical forensic evidence (footprint, dropped tool)

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
class EpistemicAtom:
    atom_id: str
    title: str
    content: str
    status: EpistemicStatus
    visibility: VisibilityTier
    carrier_type: CarrierType = CarrierType.MIND
    subject_id: Optional[str] = None
    actor_id: Optional[str] = None
    location_id: Optional[str] = None
    credibility: float = 1.0
    distortion: float = 0.0
    emotional_relevance: float = 1.0
    created_tick: int = 0
    tags: List[str] = field(default_factory=list)
    associative_keys: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "title": self.title,
            "content": self.content,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "visibility": self.visibility.value if hasattr(self.visibility, "value") else str(self.visibility),
            "carrier_type": self.carrier_type.value if hasattr(self.carrier_type, "value") else str(self.carrier_type),
            "subject_id": self.subject_id,
            "actor_id": self.actor_id,
            "location_id": self.location_id,
            "credibility": round(self.credibility, 3),
            "distortion": round(self.distortion, 3),
            "emotional_relevance": round(self.emotional_relevance, 2),
            "created_tick": self.created_tick,
            "tags": self.tags,
            "associative_keys": self.associative_keys,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpistemicAtom":
        return cls(
            atom_id=data["atom_id"],
            title=data.get("title", "Epistemic Atom"),
            content=data.get("content", ""),
            status=EpistemicStatus(data.get("status", "FACT")),
            visibility=VisibilityTier(data.get("visibility", "PUBLIC_SETTLEMENT")),
            carrier_type=CarrierType(data.get("carrier_type", "MIND")),
            subject_id=data.get("subject_id"),
            actor_id=data.get("actor_id"),
            location_id=data.get("location_id"),
            credibility=float(data.get("credibility", 1.0)),
            distortion=float(data.get("distortion", 0.0)),
            emotional_relevance=float(data.get("emotional_relevance", 1.0)),
            created_tick=int(data.get("created_tick", 0)),
            tags=list(data.get("tags", [])),
            associative_keys=list(data.get("associative_keys", [])),
            payload=dict(data.get("payload", {}))
        )


@dataclass
class EpistemicMemoryTrace:
    atom_id: str
    atom: EpistemicAtom
    salience: float = 1.0
    last_recalled_tick: int = 0
    repetition_count: int = 1
    is_confided: bool = False
    confided_by_id: Optional[str] = None

    def is_dormant(self, threshold: float = 0.15) -> bool:
        """A memory is dormant if salience dropped below threshold, unless it is a permanent emotional anchor."""
        if self.salience <= 0.0:
            return True
        if self.atom.emotional_relevance >= 1.8:
            return False  # Life anchor / trauma / pinnacle joy never slips into complete dormancy unless cleared
        return self.salience < threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "atom": self.atom.to_dict(),
            "salience": round(self.salience, 3),
            "is_dormant": self.is_dormant(),
            "last_recalled_tick": self.last_recalled_tick,
            "repetition_count": self.repetition_count,
            "is_confided": self.is_confided,
            "confided_by_id": self.confided_by_id
        }


@dataclass
class DyadicConversationThread:
    interlocutor_id: str
    discussed_atom_ids: List[str] = field(default_factory=list)
    unresolved_commitments: List[Dict[str, Any]] = field(default_factory=list)
    last_conversed_tick: int = 0
    shared_secrets_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interlocutor_id": self.interlocutor_id,
            "discussed_atom_ids": self.discussed_atom_ids,
            "unresolved_commitments": self.unresolved_commitments,
            "last_conversed_tick": self.last_conversed_tick,
            "shared_secrets_count": self.shared_secrets_count
        }


@dataclass
class PhysicalInscribedCarrier:
    item_instance_id: str
    title: str
    carrier_type: CarrierType
    inscribed_atom_ids: List[str] = field(default_factory=list)
    author_id: Optional[str] = None
    created_tick: int = 0
    is_locked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_instance_id": self.item_instance_id,
            "title": self.title,
            "carrier_type": self.carrier_type.value,
            "inscribed_atom_ids": self.inscribed_atom_ids,
            "author_id": self.author_id,
            "created_tick": self.created_tick,
            "is_locked": self.is_locked,
            "metadata": self.metadata
        }


class EpistemicEngine:
    """
    Master Epistemic Information, Memory Priming, and Knowledge Carrier Engine.
    Coordinates:
    1. Multi-axial Epistemic Atoms (Fact, Presumption, Assumption, Guess, Internal Thought, Tutorial)
    2. Visibility Tiers (Internal Mind, Secret, Confidential, Private Dyadic, Public Settlement)
    3. Inscribed Physical Carriers (Books, Ledgers, Notes, Letters, Clues)
    4. Continuous Associative Recall & Dormant Memory Priming (Actor, Location, Keyword Cues)
    5. Dyadic Conversation Threads & Context Continuity
    6. Relational Social Attention Prioritization
    7. Crime Forensic Atoms & Suspect Inference Generation
    """
    _instance: Optional["EpistemicEngine"] = None

    @classmethod
    def get_instance(cls) -> "EpistemicEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.atoms: Dict[str, EpistemicAtom] = {}
        # npc_id -> {atom_id: EpistemicMemoryTrace}
        self.npc_memories: Dict[str, Dict[str, EpistemicMemoryTrace]] = {}
        # npc_id -> {partner_id: DyadicConversationThread}
        self.dyadic_threads: Dict[str, Dict[str, DyadicConversationThread]] = {}
        # item_instance_id -> PhysicalInscribedCarrier
        self.inscribed_carriers: Dict[str, PhysicalInscribedCarrier] = {}
        # location_id -> List[EpistemicAtom]
        self.room_clues: Dict[str, List[EpistemicAtom]] = {}
        # room_id -> List[EpistemicAtom] pinned on the physical notice board
        self.room_notice_boards: Dict[str, List[EpistemicAtom]] = {}

        # Statistics
        self.total_notice_board_posts: int = 0
        self.total_notice_board_reads: int = 0
        self.total_landmarks_learned: int = 0
        self.total_atoms_created: int = 0
        self.total_priming_recalls: int = 0
        self.total_carriers_read: int = 0
        self.total_crimes_recorded: int = 0
        self.total_clues_discovered: int = 0
        self.total_inferences_generated: int = 0
        self.total_reminisce_events: int = 0

    def clear(self) -> None:
        self.atoms.clear()
        self.npc_memories.clear()
        self.dyadic_threads.clear()
        self.inscribed_carriers.clear()
        self.room_clues.clear()
        self.room_notice_boards.clear()
        self.total_notice_board_posts = 0
        self.total_notice_board_reads = 0
        self.total_landmarks_learned = 0
        self.total_atoms_created = 0
        self.total_priming_recalls = 0
        self.total_carriers_read = 0
        self.total_crimes_recorded = 0
        self.total_clues_discovered = 0
        self.total_inferences_generated = 0
        self.total_reminisce_events = 0

    def get_system_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("epistemic_system").get("epistemic_system", {})

    # -------------------------------------------------------------------------
    # 1. Epistemic Atom Creation & Registration
    # -------------------------------------------------------------------------
    def create_atom(
        self,
        title: str,
        content: str,
        status: EpistemicStatus = EpistemicStatus.FACT,
        visibility: VisibilityTier = VisibilityTier.PUBLIC_SETTLEMENT,
        carrier_type: CarrierType = CarrierType.MIND,
        subject_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        location_id: Optional[str] = None,
        credibility: Optional[float] = None,
        distortion: float = 0.0,
        emotional_relevance: float = 1.0,
        created_tick: int = 0,
        tags: Optional[List[str]] = None,
        associative_keys: Optional[List[str]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> EpistemicAtom:
        cfg = self.get_system_config()
        type_cfg = cfg.get("epistemic_types", {}).get(status.value if hasattr(status, "value") else str(status), {})
        cred = credibility if credibility is not None else float(type_cfg.get("base_credibility", 1.0))

        atom_id = f"atom_{uuid.uuid4().hex[:8]}"
        all_tags = list(tags or [])
        all_cues = list(associative_keys or [])
        if subject_id and subject_id not in all_cues:
            all_cues.append(subject_id.lower())
        if actor_id and actor_id not in all_cues:
            all_cues.append(actor_id.lower())
        if location_id and location_id not in all_cues:
            all_cues.append(location_id.lower())

        atom = EpistemicAtom(
            atom_id=atom_id,
            title=title,
            content=content,
            status=status,
            visibility=visibility,
            carrier_type=carrier_type,
            subject_id=subject_id,
            actor_id=actor_id,
            location_id=location_id,
            credibility=cred,
            distortion=distortion,
            emotional_relevance=emotional_relevance,
            created_tick=created_tick,
            tags=all_tags,
            associative_keys=all_cues,
            payload=dict(payload or {})
        )
        self.atoms[atom_id] = atom
        self.total_atoms_created += 1
        return atom

    def impart_knowledge(
        self,
        npc: Any,
        atom: EpistemicAtom,
        current_tick: int,
        salience: float = 1.0,
        confided_by_id: Optional[str] = None
    ) -> EpistemicMemoryTrace:
        """Embeds or consolidates an epistemic atom in an agent's memory."""
        traces = self.npc_memories.setdefault(npc.id, {})
        cfg = self.get_system_config()
        boost = float(cfg.get("memory_dynamics", {}).get("repetition_reinforcement_boost", 0.25))

        if atom.atom_id in traces:
            trace = traces[atom.atom_id]
            trace.salience = min(1.0, trace.salience + boost)
            trace.last_recalled_tick = current_tick
            trace.repetition_count += 1
            trace.atom.credibility = min(1.0, max(trace.atom.credibility, atom.credibility))
            return trace

        # Semantic de-duplication: check if an existing trace has identical title and content
        for existing_trace in traces.values():
            if existing_trace.atom.title == atom.title and existing_trace.atom.content == atom.content:
                existing_trace.salience = min(1.0, existing_trace.salience + boost)
                existing_trace.last_recalled_tick = current_tick
                existing_trace.repetition_count += 1
                return existing_trace
        else:
            trace = EpistemicMemoryTrace(
                atom_id=atom.atom_id,
                atom=atom,
                salience=min(1.0, max(0.1, salience)),
                last_recalled_tick=current_tick,
                repetition_count=1,
                is_confided=(confided_by_id is not None),
                confided_by_id=confided_by_id
            )
            traces[atom.atom_id] = trace

        return traces[atom.atom_id]

    # -------------------------------------------------------------------------
    # 2. Continuous Memory Forgetting & Associative Priming (Cue-Driven Recall)
    # -------------------------------------------------------------------------
    def apply_memory_decay(self, npc: Any, current_tick: int, delta_ticks: int = 1) -> None:
        """Applies exponential half-life decay to an NPC's conscious memory salience."""
        cfg = self.get_system_config()
        mem_cfg = cfg.get("memory_dynamics", {})
        half_life = float(mem_cfg.get("forgetting_half_life_ticks", 4320))
        decay_rate = math.log(2.0) / max(60.0, half_life)
        perm_thresh = float(mem_cfg.get("emotional_anchor_permanence_threshold", 1.8))

        traces = self.npc_memories.get(npc.id, {})
        for trace in traces.values():
            if trace.atom.status == EpistemicStatus.TUTORIAL_EXPLANATION:
                continue  # Practical how-to knowledge is permanent
            if trace.atom.emotional_relevance >= perm_thresh:
                # Permanent emotional anchor: stays conscious or at minimum salience buffer
                trace.salience = max(0.40, trace.salience - (decay_rate * 0.10 * delta_ticks))
                continue

            decay = decay_rate * delta_ticks
            trace.salience = max(0.01, trace.salience - decay)

    def evaluate_associative_priming(
        self,
        npc: Any,
        cues: List[str],
        context: Any,
        current_tick: int
    ) -> List[EpistemicMemoryTrace]:
        """
        Sensory & Semantic Priming:
        Cues (person seen, room entered, topic spoken) match dormant memory traces,
        spiking their salience back into active working memory!
        """
        if not cues:
            return []

        cfg = self.get_system_config()
        mem_cfg = cfg.get("memory_dynamics", {})
        sensitivity = float(mem_cfg.get("recall_cue_sensitivity", 0.65))
        dormant_thresh = float(mem_cfg.get("dormant_activation_threshold", 0.15))

        clean_cues = [c.lower().strip() for c in cues if c]
        traces = self.npc_memories.get(npc.id, {})
        reactivated = []

        for trace in traces.values():
            if not trace.is_dormant(dormant_thresh):
                continue  # Already actively conscious

            # Calculate cue match strength
            match_count = 0
            for cue in clean_cues:
                for k in trace.atom.associative_keys:
                    if cue == k or cue in k:
                        match_count += 1
                        break
                for tag in trace.atom.tags:
                    if cue == tag.lower():
                        match_count += 1
                        break

            if match_count > 0:
                boost = min(0.85, (match_count * sensitivity * 0.40) * (trace.atom.emotional_relevance / 1.0))
                trace.salience = min(1.0, trace.salience + boost)
                trace.last_recalled_tick = current_tick

                if trace.salience >= dormant_thresh:
                    reactivated.append(trace)
                    self.total_priming_recalls += 1

                    # Character biographical reflection on recall
                    if trace.atom.emotional_relevance >= 1.3:
                        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
                        npc.record_biographical_entry(
                            current_tick, time_iso, "MEMORY_REKINDLED",
                            f"Encountering cues ({', '.join(clean_cues[:2])}) brought dormant memory of '{trace.atom.title}' surging back to mind."
                        )

        return reactivated

    def get_active_working_memory(self, npc: Any, current_tick: int) -> List[EpistemicMemoryTrace]:
        """Returns conscious memory traces bounded strictly to Miller's 7 +/- 2 capacity."""
        cfg = self.get_system_config()
        cap = int(cfg.get("memory_dynamics", {}).get("working_memory_capacity", 7))
        dormant_thresh = float(cfg.get("memory_dynamics", {}).get("dormant_activation_threshold", 0.15))

        traces = self.npc_memories.get(npc.id, {})
        active = [
            t for t in traces.values()
            if not t.is_dormant(dormant_thresh)
        ]
        # Sort by salience weighted by personal emotional relevance
        active.sort(key=lambda t: t.salience * t.atom.emotional_relevance, reverse=True)
        return active[:cap]

    # -------------------------------------------------------------------------
    # 3. Physical Inscribed Carriers (Books, Ledgers, Notes, Letters, Clues)
    # -------------------------------------------------------------------------
    def inscribe_physical_carrier(
        self,
        item_instance: Any,
        title: str,
        carrier_type: CarrierType,
        atoms: List[EpistemicAtom],
        author_id: Optional[str] = None,
        created_tick: int = 0,
        is_locked: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PhysicalInscribedCarrier:
        """Inscribes physical media with permanent or confidential epistemic atoms."""
        atom_ids = [a.atom_id for a in atoms]
        for a in atoms:
            a.carrier_type = carrier_type
            self.atoms[a.atom_id] = a

        carrier = PhysicalInscribedCarrier(
            item_instance_id=item_instance.instance_id,
            title=title,
            carrier_type=carrier_type,
            inscribed_atom_ids=atom_ids,
            author_id=author_id,
            created_tick=created_tick,
            is_locked=is_locked,
            metadata=dict(metadata or {})
        )
        self.inscribed_carriers[item_instance.instance_id] = carrier
        return carrier

    def read_inscribed_carrier(
        self,
        reader: Any,
        item_instance: Any,
        context: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """
        Reader reads an inscribed physical book, ledger, or note:
        - Transfers all inscribed atoms into reader's memory.
        - Unlocks trade knowledge / recipe boosts from books.
        - Unlocks confidential financial facts from municipal ledgers.
        """
        carrier = self.inscribed_carriers.get(item_instance.instance_id)
        if not carrier:
            return {"success": False, "reason": "Item has no inscribed text or legible carrier."}

        if carrier.is_locked:
            return {"success": False, "reason": "Carrier is locked with a cipher seal."}

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        learned_atoms = []

        for a_id in carrier.inscribed_atom_ids:
            atom = self.atoms.get(a_id)
            if atom:
                self.impart_knowledge(reader, atom, current_tick, salience=1.0)
                learned_atoms.append(atom)

        # Apply carrier-specific learning or utility effects
        skill_boost = 0.0
        if carrier.carrier_type == CarrierType.BOOK:
            teaches_skill = carrier.metadata.get("teaches_skill", "crafting")
            if teaches_skill in getattr(reader, "skills", {}):
                cur = reader.skills[teaches_skill]
                skill_boost = 2.0
                reader.skills[teaches_skill] = round(cur + skill_boost, 2)
            reader.adjust_feeling("contentment", 10.0)

        elif carrier.carrier_type == CarrierType.LEDGER:
            reader.adjust_feeling("pride", 8.0)

        elif carrier.carrier_type in (CarrierType.LETTER, CarrierType.NOTE):
            reader.adjust_feeling("tenderness", 12.0)

        reader.record_biographical_entry(
            current_tick, time_iso, "READ_INSCRIBED_CARRIER",
            f"Read {carrier.carrier_type.value.lower()} '{carrier.title}', acquiring {len(learned_atoms)} epistemic atoms."
        )

        self.total_carriers_read += 1
        return {
            "success": True,
            "title": carrier.title,
            "carrier_type": carrier.carrier_type.value,
            "atoms_learned_count": len(learned_atoms),
            "skill_boost": skill_boost
        }

    # -------------------------------------------------------------------------
    # 4. Forensic Crime Investigation & Clues
    # -------------------------------------------------------------------------
    def record_crime_forensic_atoms(
        self,
        perpetrator: Any,
        victim: Optional[Any],
        crime_type: str,
        location_id: str,
        context: Any,
        current_tick: int
    ) -> Dict[str, EpistemicAtom]:
        """
        Creates forensic epistemic atoms upon commission of a crime:
        1. ACT_ATOM: Internal truth held by perpetrator.
        2. INCIDENT_ATOM: Public reality observed by victim / town.
        3. CLUE_ATOM: Physical evidence left in the room (boot print, dropped lockpick).
        """
        # 1. Secret Act Atom (Perpetrator)
        act_atom = self.create_atom(
            title=f"Secret Crime: {crime_type}",
            content=f"{perpetrator.name} committed {crime_type} at {location_id}.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.SECRET,
            carrier_type=CarrierType.MIND,
            subject_id=victim.id if victim else None,
            actor_id=perpetrator.id,
            location_id=location_id,
            emotional_relevance=2.0,
            created_tick=current_tick,
            tags=["crime", crime_type.lower(), "guilt"],
            associative_keys=[perpetrator.id, location_id, "crime", crime_type.lower()]
        )
        self.impart_knowledge(perpetrator, act_atom, current_tick, salience=1.0)

        # 2. Public Incident Atom
        victim_name = victim.name if victim else "local stores"
        incident_atom = self.create_atom(
            title=f"Crime Incident: {crime_type}",
            content=f"{crime_type} occurred at {location_id} targeting {victim_name}.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.PUBLIC_SETTLEMENT,
            carrier_type=CarrierType.MIND,
            subject_id=victim.id if victim else None,
            location_id=location_id,
            emotional_relevance=1.5,
            created_tick=current_tick,
            tags=["crime", "incident", crime_type.lower()],
            associative_keys=[location_id, "crime", crime_type.lower()]
        )
        if victim:
            self.impart_knowledge(victim, incident_atom, current_tick, salience=1.0)

        # 3. Physical Clue Atom (Left in Room)
        clue_atom = self.create_atom(
            title=f"Forensic Clue: Evidence of {crime_type}",
            content=f"Scuffed boot prints and tool marks left at {location_id} matching {perpetrator.occupation.lower()} gear.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.CONFIDENTIAL,
            carrier_type=CarrierType.PHYSICAL_CLUE,
            actor_id=perpetrator.id,
            location_id=location_id,
            credibility=0.90,
            emotional_relevance=1.4,
            created_tick=current_tick,
            tags=["clue", "evidence", crime_type.lower()],
            associative_keys=[location_id, perpetrator.id, "clue", "evidence"],
            payload={"suspect_id": perpetrator.id, "crime_type": crime_type}
        )
        self.room_clues.setdefault(location_id, []).append(clue_atom)
        self.total_crimes_recorded += 1

        return {
            "act_atom": act_atom,
            "incident_atom": incident_atom,
            "clue_atom": clue_atom
        }

    def investigate_crime_scene(
        self,
        investigator: Any,
        location_id: str,
        context: Any,
        current_tick: int
    ) -> List[EpistemicAtom]:
        """
        Town Guard or investigator inspects location_id for physical clues:
        - Discovers forensic clue atoms.
        - Generates high-confidence PRESUMPTION suspect inference atom.
        """
        clues = self.room_clues.get(location_id, [])
        if not clues:
            return []

        discovered = []
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        for clue in list(clues):
            self.impart_knowledge(investigator, clue, current_tick, salience=1.0)
            discovered.append(clue)
            self.total_clues_discovered += 1

            suspect_id = clue.payload.get("suspect_id")
            crime_type = clue.payload.get("crime_type", "transgression")

            if suspect_id and hasattr(context, "npcs") and suspect_id in context.npcs:
                suspect = context.npcs[suspect_id]
                # Formulate deductive PRESUMPTION suspect atom
                presumption = self.create_atom(
                    title=f"Suspect Inference: {suspect.name}",
                    content=f"Physical forensic clue at {location_id} links {suspect.name} to the {crime_type}.",
                    status=EpistemicStatus.PRESUMPTION,
                    visibility=VisibilityTier.CONFIDENTIAL,
                    carrier_type=CarrierType.MIND,
                    subject_id=suspect.id,
                    location_id=location_id,
                    credibility=0.80,
                    emotional_relevance=1.6,
                    created_tick=current_tick,
                    tags=["suspect", "warrant", crime_type.lower()],
                    associative_keys=[suspect.id, location_id, "suspect"],
                    payload={"suspect_id": suspect.id, "warrant_active": True}
                )
                self.impart_knowledge(investigator, presumption, current_tick, salience=1.0)
                discovered.append(presumption)
                self.total_inferences_generated += 1

                investigator.record_biographical_entry(
                    current_tick, time_iso, "CRIME_SCENE_INVESTIGATED",
                    f"Discovered forensic clue at {location_id} and identified {suspect.name} as prime suspect in {crime_type}."
                )

        # Clear discovered physical clues from scene
        self.room_clues[location_id] = []
        return discovered

    # -------------------------------------------------------------------------
    # 5. Dyadic Conversation Threads & Relationship Prioritization
    # -------------------------------------------------------------------------
    def get_dyadic_thread(self, npc_a_id: str, npc_b_id: str) -> DyadicConversationThread:
        threads = self.dyadic_threads.setdefault(npc_a_id, {})
        if npc_b_id not in threads:
            threads[npc_b_id] = DyadicConversationThread(interlocutor_id=npc_b_id)
        return threads[npc_b_id]

    def record_dyadic_exchange(
        self,
        speaker: Any,
        listener: Any,
        atom: EpistemicAtom,
        context: Any,
        current_tick: int
    ) -> None:
        """Records shared atom in dyadic thread, updating shared secrets and context continuity."""
        thread_a = self.get_dyadic_thread(speaker.id, listener.id)
        thread_b = self.get_dyadic_thread(listener.id, speaker.id)

        thread_a.last_conversed_tick = current_tick
        thread_b.last_conversed_tick = current_tick

        if atom.atom_id not in thread_a.discussed_atom_ids:
            thread_a.discussed_atom_ids.append(atom.atom_id)
        if atom.atom_id not in thread_b.discussed_atom_ids:
            thread_b.discussed_atom_ids.append(atom.atom_id)

        if atom.visibility in (VisibilityTier.SECRET, VisibilityTier.CONFIDENTIAL):
            thread_a.shared_secrets_count += 1
            thread_b.shared_secrets_count += 1

    def calculate_relational_priority(self, npc: Any, other_npc: Any, context: Any) -> float:
        """
        Continuous Relational Social Attention Budget:
        Prioritizes interactions based on spousal devotion, directional trust,
        club kinship, and life goal alignment.
        """
        cfg = self.get_system_config()
        weights = cfg.get("relationship_priority_weights", {})
        w_spouse = float(weights.get("spousal_affection_weight", 0.40))
        w_trust = float(weights.get("trust_weight", 0.30))
        w_club = float(weights.get("club_kinship_weight", 0.15))
        w_goal = float(weights.get("aspirational_utility_weight", 0.15))

        sp = getattr(npc, "social_profile", {}) or {}
        is_spouse = bool(sp.get("spouse_id") == other_npc.id or sp.get("partner_id") == other_npc.id)

        # 1. Spousal factor
        spouse_score = 100.0 if is_spouse else 0.0

        # 2. Trust & opinion
        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        trust_score = float(op_eng.get_net_opinion(npc.id, other_npc.id)) if op_eng and hasattr(op_eng, "get_net_opinion") else 50.0
        trust_score = max(0.0, min(100.0, trust_score + 50.0))

        # 3. Club Kinship
        club_eng = context.get_service("social_club_engine") if hasattr(context, "get_service") else None
        club_kinship = 0.0
        if club_eng and hasattr(club_eng, "clubs"):
            for club in club_eng.clubs.values():
                if npc.id in club.member_ids and other_npc.id in club.member_ids:
                    club_kinship = 100.0
                    break

        # 4. Aspirational Alignment
        goal_score = 50.0
        lg_eng = context.get_service("life_goal_engine") if hasattr(context, "get_service") else None
        if lg_eng:
            goal = lg_eng.get_agent_goal(npc.id)
            if goal:
                if goal.id == "DEVOTED_SPOUSE" and is_spouse:
                    goal_score = 100.0
                elif goal.id == "MASTER_ARTISAN" and club_kinship > 50.0:
                    goal_score = 90.0
                elif goal.id == "DYNASTIC_MERCHANT" and any(k in (other_npc.occupation or "").lower() for k in ("merchant", "mayor", "notary")):
                    goal_score = 85.0

        score = (spouse_score * w_spouse) + (trust_score * w_trust) + (club_kinship * w_club) + (goal_score * w_goal)
        return round(score, 2)

    # -------------------------------------------------------------------------
    # 6. Life History Reflection & Reminiscing
    # -------------------------------------------------------------------------
    def reminisce_life_event(self, npc: Any, context: Any, current_tick: int) -> Optional[Dict[str, Any]]:
        """
        Agent introspects on high-emotion life event anchor atoms (emotional_relevance >= 1.8).
        Restores contentment, primes romantic affection, or increases vigilance based on past trauma.
        """
        traces = self.npc_memories.get(npc.id, {})
        anchors = [
            t for t in traces.values()
            if t.atom.emotional_relevance >= 1.8
        ]
        if not anchors:
            return None

        # Sample one anchor event
        anchor = anchors[0]
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        outcome = {"title": anchor.atom.title, "event_type": anchor.atom.status.value}

        if "marriage" in anchor.atom.tags or "betrothal" in anchor.atom.tags or "love" in anchor.atom.tags:
            npc.adjust_feeling("tenderness", 15.0)
            npc.adjust_feeling("contentment", 12.0)
            outcome["effect"] = "rekindled_tenderness"
        elif "crime" in anchor.atom.tags or "theft" in anchor.atom.tags:
            npc.adjust_feeling("vigilance" if "vigilance" in getattr(npc, "feelings", {}) else "stress", 10.0)
            outcome["effect"] = "heightened_vigilance"
        else:
            npc.adjust_feeling("contentment", 8.0)
            outcome["effect"] = "nostalgic_contentment"

        anchor.salience = 1.0
        anchor.last_recalled_tick = current_tick
        self.total_reminisce_events += 1

        npc.record_biographical_entry(
            current_tick, time_iso, "REMINISCE_PAST",
            f"Quietly reminisced over pivotal life event '{anchor.atom.title}', reflecting on its significance."
        )
        return outcome

    # -------------------------------------------------------------------------
    # 7. Physical Room-Anchored Notice Boards
    # -------------------------------------------------------------------------
    def post_to_notice_board(self, room_id: str, atom: EpistemicAtom) -> EpistemicAtom:
        """Pins an epistemic atom to the physical notice board in room_id."""
        self.atoms[atom.atom_id] = atom
        self.room_notice_boards.setdefault(room_id, []).append(atom)
        self.total_notice_board_posts += 1
        return atom

    def get_notice_board_atoms(self, room_id: str) -> List[EpistemicAtom]:
        """Returns all active atoms pinned to the room notice board."""
        return list(self.room_notice_boards.get(room_id, []))

    def read_notice_board(
        self,
        reader: Any,
        room_id: str,
        context: Any,
        current_tick: int,
        log_biography: bool = True
    ) -> List[EpistemicAtom]:
        """Reader scans the physical notice board in room_id, acquiring newly discovered atoms into working memory."""
        board_atoms = self.room_notice_boards.get(room_id, [])
        if not board_atoms:
            return []

        reader_traces = self.npc_memories.setdefault(reader.id, {})
        newly_learned = []

        for atom in board_atoms:
            # Check if already in traces by id or semantic match
            already_known = (atom.atom_id in reader_traces) or any(
                t.atom.title == atom.title and t.atom.content == atom.content for t in reader_traces.values()
            )
            if not already_known:
                self.impart_knowledge(reader, atom, current_tick, salience=1.0, confided_by_id=atom.actor_id)
                newly_learned.append(atom)
            else:
                trace = reader_traces.get(atom.atom_id)
                if not trace:
                    trace = next(t for t in reader_traces.values() if t.atom.title == atom.title and t.atom.content == atom.content)
                trace.salience = min(1.0, trace.salience + 0.35)
                trace.last_recalled_tick = current_tick

        if newly_learned and log_biography:
            self.total_notice_board_reads += 1
            time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
            titles = ", ".join(a.title for a in newly_learned[:2])
            reader.record_biographical_entry(
                current_tick, time_iso, "READ_ROOM_NOTICE_BOARD",
                f"Read physical notice board at {room_id}, learning: {titles}."
            )

        return newly_learned

    # -------------------------------------------------------------------------
    # 8. Spatial Landmark Learning & Topological Mental Map
    # -------------------------------------------------------------------------
    def learn_spatial_landmark(
        self,
        npc: Any,
        room_id: str,
        room_name: str,
        connected_rooms: List[str],
        context: Any,
        current_tick: int = 0
    ) -> EpistemicAtom:
        """Records a physical spatial landmark and connections into an NPC's mental map and epistemic memory."""
        m_map = getattr(npc, "mental_map", None)
        if m_map is None:
            npc.mental_map = {}
            m_map = npc.mental_map

        discovered = m_map.setdefault("discovered_rooms", set())
        connections = m_map.setdefault("known_connections", {})
        landmarks = m_map.setdefault("landmarks", {})

        discovered.add(room_id)
        connections[room_id] = list(connected_rooms)

        atom = self.create_atom(
            title=f"Landmark: {room_name}",
            content=f"{room_name} ({room_id}) connects to {', '.join(connected_rooms)}.",
            status=EpistemicStatus.FACT,
            visibility=VisibilityTier.INTERNAL_MIND,
            carrier_type=CarrierType.MIND,
            location_id=room_id,
            emotional_relevance=0.40,
            created_tick=current_tick,
            tags=["spatial", "landmark", room_id.lower()],
            associative_keys=[room_id.lower(), "landmark", "direction"],
            payload={"room_id": room_id, "room_name": room_name, "connected_rooms": connected_rooms}
        )
        landmarks[room_id] = atom.atom_id
        self.impart_knowledge(npc, atom, current_tick, salience=1.0)
        self.total_landmarks_learned += 1
        return atom

    def share_spatial_directions(
        self,
        speaker: Any,
        listener: Any,
        target_room_id: str,
        context: Any,
        current_tick: int = 0
    ) -> Optional[EpistemicAtom]:
        """Speaker provides directions to target_room_id to listener, transferring spatial knowledge."""
        sp_map = getattr(speaker, "mental_map", {})
        if target_room_id not in sp_map.get("discovered_rooms", set()):
            return None

        connections = sp_map.get("known_connections", {}).get(target_room_id, [])
        room_name = target_room_id.replace("room_", "").replace("_", " ").title()

        atom = self.learn_spatial_landmark(listener, target_room_id, room_name, connections, context, current_tick)

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        listener.record_biographical_entry(
            current_tick, time_iso, "LEARNED_DIRECTIONS",
            f"Received travel directions to {room_name} from {speaker.name}, expanding mental map."
        )
        return atom
