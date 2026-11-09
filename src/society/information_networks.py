"""
Unified Information & Communication Engine.
Consolidates all settlement communication avenues—civic notice boards, peer gossip/rumors,
watch crime reporting, underworld shadow intelligence (wealthy marks), and vocational instruction—
into a single, decoupled, data-driven information diffusion system.
Now enhanced with:
1. Epistemic Memory Traces & Continuous Salience Decay (Borchert Memory Half-life)
2. Ambient Spatial Affordance Waves (Visual line-of-sight & Acoustic doorway propagation)
3. Receiver-Centric Pull with Cognitive Bandwidth & Emotional Biases
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from src.entities.npc import NPC
from src.configuration.settings import SettingsRegistry

class InformationChannelType(str, Enum):
    CIVIC_NOTICES = "CIVIC_NOTICES"             # Public boards, decrees, official postings
    GOSSIP_AND_RUMORS = "GOSSIP_AND_RUMORS"     # Peer-to-peer word-of-mouth news and scandals
    CRIME_AND_JUSTICE = "CRIME_AND_JUSTICE"     # Witness crime reports, watch alerts, warrants
    SHADOW_INTELLIGENCE = "SHADOW_INTELLIGENCE" # Underworld marks, robbery targets, contraband drops
    VOCATIONAL_KNOWLEDGE = "VOCATIONAL_KNOWLEDGE" # Trade mastery, crafting tips, recipes

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

class WaveMedium(str, Enum):
    VISUAL_LINE_OF_SIGHT = "VISUAL_LINE_OF_SIGHT" # High clarity within room line-of-sight
    ACOUSTIC_SOUND = "ACOUSTIC_SOUND"             # Audible in room and spills through doorways

@dataclass
class EpistemicMemoryTrace:
    item_id: str
    learned_tick: int
    salience: float = 1.0               # 0.0 to 1.0 (decays exponentially over time)
    emotional_relevance: float = 1.0    # Stake multiplier (personal stake keeps memory salient longer)
    last_recalled_tick: int = 0
    distortion_observed: float = 0.0
    credibility_observed: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "learned_tick": self.learned_tick,
            "salience": round(self.salience, 3),
            "emotional_relevance": round(self.emotional_relevance, 2),
            "last_recalled_tick": self.last_recalled_tick,
            "distortion_observed": round(self.distortion_observed, 2),
            "credibility_observed": round(self.credibility_observed, 2)
        }

@dataclass
class AmbientInformationWave:
    wave_id: str
    item_id: str
    origin_room_id: str
    current_room_id: str
    medium: WaveMedium
    intensity: float = 1.0              # 0.0 to 1.0
    created_tick: int = 0
    duration_ticks: int = 60
    hops: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave_id": self.wave_id,
            "item_id": self.item_id,
            "origin_room_id": self.origin_room_id,
            "current_room_id": self.current_room_id,
            "medium": self.medium.value if hasattr(self.medium, "value") else str(self.medium),
            "intensity": round(self.intensity, 2),
            "created_tick": self.created_tick,
            "duration_ticks": self.duration_ticks,
            "hops": self.hops
        }

@dataclass
class InformationItem:
    item_id: str
    channel: InformationChannelType
    topic: str
    headline: str
    content: str
    source_npc_id: Optional[str] = None
    subject_npc_id: Optional[str] = None
    target_location_id: Optional[str] = None
    credibility: float = 0.85
    distortion: float = 0.0
    hop_count: int = 0
    created_tick: int = 0
    expires_tick: int = 14400
    is_active: bool = True
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "channel": self.channel.value if hasattr(self.channel, "value") else str(self.channel),
            "topic": self.topic,
            "headline": self.headline,
            "content": self.content,
            "source_npc_id": self.source_npc_id,
            "subject_npc_id": self.subject_npc_id,
            "target_location_id": self.target_location_id,
            "credibility": round(self.credibility, 2),
            "distortion": round(self.distortion, 2),
            "hop_count": self.hop_count,
            "created_tick": self.created_tick,
            "expires_tick": self.expires_tick,
            "is_active": self.is_active,
            "payload": self.payload
        }

class UnifiedInformationEngine:
    """
    Central Information & Communication Engine.
    Handles all communication types, perception filtering, rumor propagation,
    crime alerts to guards, shadow mark discoveries, and trade mentorship.
    Enhanced with continuous Borchert memory half-lives and ambient affordance waves.
    """
    _instance: Optional["UnifiedInformationEngine"] = None

    @classmethod
    def get_instance(cls) -> "UnifiedInformationEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.active_items: Dict[str, InformationItem] = {}
        self.item_history: List[InformationItem] = []

        # Epistemic Memory Traces: npc_id -> {item_id: EpistemicMemoryTrace}
        self.npc_memory_traces: Dict[str, Dict[str, EpistemicMemoryTrace]] = {}
        # Backward-compatible set view: npc_id -> Set[item_id]
        self.npc_knowledge_ledger: Dict[str, Set[str]] = {}

        # Ambient spatial waves active in the environment
        self.active_waves: List[AmbientInformationWave] = []

        # Statistics
        self.total_rumors_diffused: int = 0
        self.total_crimes_reported_to_watch: int = 0
        self.total_shadow_marks_appraised: int = 0
        self.total_notices_read: int = 0
        self.total_vocational_lessons: int = 0
        self.total_memories_evicted: int = 0
        self.total_ambient_perceptions: int = 0

    def get_channel_config(self, channel: InformationChannelType) -> Dict[str, Any]:
        settings = SettingsRegistry.get_instance().get("information_networks")
        ch_key = channel.value if hasattr(channel, "value") else str(channel)
        return settings.get("channels", {}).get(ch_key, {})

    def record_learned_item(
        self,
        npc_id: str,
        item_id: str,
        current_tick: int,
        emotional_relevance: float = 1.0,
        credibility: float = 0.85,
        distortion: float = 0.0
    ) -> EpistemicMemoryTrace:
        """
        Records or reinforces an information item in an NPC's epistemic memory.
        If already known, applies memory consolidation (salience boost).
        """
        traces = self.npc_memory_traces.setdefault(npc_id, {})
        known_set = self.npc_knowledge_ledger.setdefault(npc_id, set())

        cfg = SettingsRegistry.get_instance().get("information_networks")
        mem_cfg = cfg.get("memory_dynamics", {})
        boost = float(mem_cfg.get("recall_salience_boost", 0.35))
        cap = float(mem_cfg.get("repetition_reinforcement_cap", 1.0))

        if item_id in traces:
            trace = traces[item_id]
            trace.salience = min(cap, trace.salience + boost)
            trace.last_recalled_tick = current_tick
            trace.emotional_relevance = max(trace.emotional_relevance, emotional_relevance)
        else:
            trace = EpistemicMemoryTrace(
                item_id=item_id,
                learned_tick=current_tick,
                salience=1.0,
                emotional_relevance=emotional_relevance,
                last_recalled_tick=current_tick,
                distortion_observed=distortion,
                credibility_observed=credibility
            )
            traces[item_id] = trace

        known_set.add(item_id)
        return traces[item_id]

    def emit_ambient_wave(
        self,
        item: InformationItem,
        origin_room_id: str,
        medium: WaveMedium = WaveMedium.VISUAL_LINE_OF_SIGHT,
        intensity: float = 1.0,
        context: Optional[Any] = None,
        current_tick: int = 0
    ) -> AmbientInformationWave:
        """
        Emits an ambient information wave into a room.
        Acoustic sound waves can propagate with attenuation across open doorways.
        """
        cfg = SettingsRegistry.get_instance().get("information_networks")
        w_cfg = cfg.get("ambient_waves", {})
        duration = int(w_cfg.get("default_wave_duration_ticks", 60))
        attenuation = float(w_cfg.get("acoustic_portal_attenuation", 0.50))
        min_intensity = float(w_cfg.get("min_perceptible_intensity", 0.15))

        wave_id = f"wave_{uuid.uuid4().hex[:8]}"
        primary_wave = AmbientInformationWave(
            wave_id=wave_id,
            item_id=item.item_id,
            origin_room_id=origin_room_id,
            current_room_id=origin_room_id,
            medium=medium,
            intensity=max(0.0, min(1.0, intensity)),
            created_tick=current_tick,
            duration_ticks=duration,
            hops=0
        )
        self.active_waves.append(primary_wave)

        # Acoustic doorway propagation to adjacent rooms along SpatialGraph
        if medium == WaveMedium.ACOUSTIC_SOUND and intensity > 0.40 and context and hasattr(context, "spatial_graph"):
            neighbors = context.spatial_graph.adj_list.get(origin_room_id, set())
            for n_room in neighbors:
                spillover = intensity * (1.0 - attenuation)
                if spillover >= min_intensity:
                    sub_wave = AmbientInformationWave(
                        wave_id=f"wave_{uuid.uuid4().hex[:8]}",
                        item_id=item.item_id,
                        origin_room_id=origin_room_id,
                        current_room_id=n_room,
                        medium=medium,
                        intensity=round(spillover, 2),
                        created_tick=current_tick,
                        duration_ticks=max(10, duration // 2),
                        hops=1
                    )
                    self.active_waves.append(sub_wave)

        return primary_wave

    def evaluate_receiver_receptivity(
        self,
        receiver: NPC,
        item: InformationItem,
        context: Any
    ) -> Tuple[bool, float]:
        """
        Receiver-Centric Pull: Evaluates whether receiver's cognitive capacity,
        fatigue, and emotional biases allow absorbing the information item.
        Returns (is_receptive, receptivity_multiplier).
        """
        cfg = SettingsRegistry.get_instance().get("information_networks")
        cog_cfg = cfg.get("cognitive_receptivity", {})

        energy = float(receiver.needs.get("energy", 100.0))
        stress = float(receiver.feelings.get("stress", 0.0))
        resentment = float(receiver.feelings.get("resentment", 0.0))
        p = getattr(receiver, "personality", {}) or {}
        cons = float(p.get("conscientiousness", 0.5))
        ext = float(p.get("extraversion", 0.5))
        honor = float(getattr(receiver, "social_profile", {}).get("moral_values", {}).get("honor", 0.5))

        # 1. Cognitive Load Filter (Elastic Working Memory)
        wm_eng = context.get_service("elastic_working_memory_engine") if context else None
        if wm_eng and hasattr(wm_eng, "get_or_create_profile"):
            prof = wm_eng.get_or_create_profile(receiver)
            if getattr(prof, "bandwidth_ratio", 1.0) < float(cog_cfg.get("min_bandwidth_ratio_for_idle_gossip", 0.30)):
                # In acute cognitive tunnel mode, filter out non-essential idle chatter
                if item.channel == InformationChannelType.GOSSIP_AND_RUMORS and "SCANDAL" not in item.topic:
                    return False, 0.0

        # 2. Somatic Exhaustion & Severe Stress Filter
        exhaust_thresh = float(cog_cfg.get("exhaustion_energy_threshold", 20.0))
        stress_thresh = float(cog_cfg.get("high_stress_threshold", 70.0))

        if (energy < exhaust_thresh or stress > stress_thresh):
            # Somatically drained citizens ignore casual rumors unless critical
            if item.channel == InformationChannelType.GOSSIP_AND_RUMORS:
                return False, 0.0

        # 3. Base receptivity
        receptivity = 0.50 + (ext * 0.25)

        # 4. Emotional & Moral Channel Affinity
        if item.channel in (InformationChannelType.CRIME_AND_JUSTICE, InformationChannelType.SHADOW_INTELLIGENCE) or any(k in item.topic for k in ("SCANDAL", "THEFT", "DEBT", "FRAUD")):
            if resentment > 25.0:
                receptivity += float(cog_cfg.get("resentment_gossip_bias", 0.25))

        if item.channel == InformationChannelType.CIVIC_NOTICES:
            receptivity += (cons * 0.20) + (honor * float(cog_cfg.get("honor_civic_bias", 0.20)))

        # 5. Discernment: highly conscientious citizens discount low-credibility rumors
        if item.credibility < 0.40 and cons > 0.60:
            receptivity *= 0.50

        return True, max(0.10, min(1.0, receptivity))

    def evict_decayed_memories(self, current_tick: int) -> int:
        """
        Continuous Epistemic Forgetting Curve (Borchert Memory Half-life).
        Prunes items whose salience has decayed below threshold and enforces capacity limits.
        Guarantees strict O(1) memory bound per citizen.
        """
        cfg = SettingsRegistry.get_instance().get("information_networks")
        mem_cfg = cfg.get("memory_dynamics", {})
        decay_lambda = float(mem_cfg.get("salience_decay_lambda", 0.0003))
        evict_thresh = float(mem_cfg.get("eviction_salience_threshold", 0.10))
        max_items = int(mem_cfg.get("max_mental_known_items_per_npc", 30))

        total_evicted = 0
        for npc_id, traces in list(self.npc_memory_traces.items()):
            known_set = self.npc_knowledge_ledger.setdefault(npc_id, set())
            evict_ids = []
            active_salience_list = []

            for item_id, trace in list(traces.items()):
                item = self.active_items.get(item_id)
                # Protected permanent civic welcome notice
                is_permanent = bool(item and item.channel == InformationChannelType.CIVIC_NOTICES and item.topic == "MUNICIPAL_WELCOME")

                elapsed = max(0, current_tick - trace.last_recalled_tick)
                salience = trace.salience * trace.emotional_relevance * math.exp(-decay_lambda * elapsed)
                trace.salience = max(0.0, min(1.0, salience))

                if salience < evict_thresh and not is_permanent:
                    evict_ids.append(item_id)
                else:
                    active_salience_list.append((item_id, salience, is_permanent))

            # Evict below threshold
            for e_id in evict_ids:
                del traces[e_id]
                known_set.discard(e_id)
                total_evicted += 1

            # Capacity limit eviction (drop lowest salience if overflowing)
            if len(traces) > max_items:
                # Sort lowest salience first, protecting permanent items
                active_salience_list.sort(key=lambda x: (x[2], x[1]))
                overflow = len(traces) - max_items
                for o_id, _, is_perm in active_salience_list[:overflow]:
                    if not is_perm and o_id in traces:
                        del traces[o_id]
                        known_set.discard(o_id)
                        total_evicted += 1

        self.total_memories_evicted += total_evicted
        return total_evicted

    def publish_item(
        self,
        channel: InformationChannelType,
        topic: str,
        headline: str,
        content: str,
        source_npc_id: Optional[str] = None,
        subject_npc_id: Optional[str] = None,
        target_location_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        custom_duration: Optional[int] = None,
        context: Optional[Any] = None
    ) -> InformationItem:
        """Publishes a new piece of information and radiates an ambient spatial wave."""
        cfg = self.get_channel_config(channel)
        decay = custom_duration or int(cfg.get("default_decay_ticks", 4320))
        cred = float(cfg.get("base_credibility", 0.80))

        item_id = f"info_{uuid.uuid4().hex[:8]}"
        item = InformationItem(
            item_id=item_id,
            channel=channel,
            topic=topic,
            headline=headline,
            content=content,
            source_npc_id=source_npc_id,
            subject_npc_id=subject_npc_id,
            target_location_id=target_location_id,
            credibility=cred,
            created_tick=current_tick,
            expires_tick=current_tick + decay,
            is_active=True,
            payload=dict(payload or {})
        )
        self.active_items[item_id] = item

        # Source NPC automatically records this item in their epistemic memory
        if source_npc_id:
            self.record_learned_item(source_npc_id, item_id, current_tick, emotional_relevance=1.5, credibility=cred)

        # Radiate ambient wave into target room if location specified
        if target_location_id:
            medium = WaveMedium.VISUAL_LINE_OF_SIGHT if channel in (InformationChannelType.CIVIC_NOTICES, InformationChannelType.SHADOW_INTELLIGENCE) else WaveMedium.ACOUSTIC_SOUND
            intensity = 0.95 if channel == InformationChannelType.CIVIC_NOTICES else 0.80
            self.emit_ambient_wave(item, target_location_id, medium=medium, intensity=intensity, context=context, current_tick=current_tick)

        # Mirror civic notices onto physical room notice board carrier in EpistemicEngine
        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng and channel == InformationChannelType.CIVIC_NOTICES:
                from src.society.epistemic_engine import EpistemicStatus, VisibilityTier, CarrierType
                atom = ep_eng.create_atom(
                    title=headline,
                    content=content,
                    status=EpistemicStatus.FACT,
                    visibility=VisibilityTier.PUBLIC_SETTLEMENT,
                    carrier_type=CarrierType.NOTE,
                    subject_id=subject_npc_id,
                    actor_id=source_npc_id,
                    location_id=target_location_id,
                    credibility=cred,
                    created_tick=current_tick,
                    tags=["notice_board", topic.lower()],
                    payload=dict(payload or {})
                )
                if target_location_id:
                    ep_eng.post_to_notice_board(target_location_id, atom)

        return item

    def get_known_items(self, npc_id: str) -> List[InformationItem]:
        """Returns all active information items currently known to a specific citizen."""
        known_ids = self.npc_knowledge_ledger.get(npc_id, set())
        return [self.active_items[i_id] for i_id in known_ids if i_id in self.active_items and self.active_items[i_id].is_active]

    # -------------------------------------------------------------------------
    # 1. CIVIC NOTICES (Notice Boards, Plaza Bulletins)
    # -------------------------------------------------------------------------
    def read_notice_board(
        self,
        reader: NPC,
        room_id: str,
        context: Any,
        current_tick: int
    ) -> List[InformationItem]:
        """Reader reads the public notice board in the current room, learning civic notices."""
        cfg = self.get_channel_config(InformationChannelType.CIVIC_NOTICES)
        allowed_kw = cfg.get("allowed_room_keywords", ["square", "hall", "plaza", "market", "board"])

        r_low = room_id.lower()
        if not any(k in r_low for k in allowed_kw):
            return []

        # Reading Cooldown: do not re-read notice board repeatedly unless new items have been posted
        last_read = getattr(reader, "_last_notice_board_read_tick", -9999)
        has_new_items = any(item.created_tick > last_read for item in self.active_items.values() if item.is_active and item.channel == InformationChannelType.CIVIC_NOTICES)
        if (current_tick - last_read < 1440) and not has_new_items and last_read != -9999:
            return []
        reader._last_notice_board_read_tick = current_tick

        learned: List[InformationItem] = []
        reader_known = self.npc_knowledge_ledger.setdefault(reader.id, set())

        for item in self.active_items.values():
            if not item.is_active or item.channel != InformationChannelType.CIVIC_NOTICES:
                continue
            if item.item_id not in reader_known:
                self.record_learned_item(reader.id, item.item_id, current_tick, emotional_relevance=1.2, credibility=item.credibility)
                learned.append(item)
                self.total_notices_read += 1

        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng:
                ep_eng.read_notice_board(reader, room_id, context, current_tick, log_biography=False)

        if learned:
            time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
            reader.record_biographical_entry(
                current_tick, time_iso, "READ_NOTICE_BOARD",
                f"Read municipal notice board at {room_id}, learning about: {', '.join(i.headline for i in learned[:2])}."
            )

        return learned

    # -------------------------------------------------------------------------
    # 2. GOSSIP & RUMOR DIFFUSION (Receiver-Centric Word-of-Mouth)
    # -------------------------------------------------------------------------
    def share_gossip(
        self,
        speaker: NPC,
        listener: NPC,
        context: Any,
        current_tick: int
    ) -> List[InformationItem]:
        """
        Speaker shares active rumors and news with listener during conversation.
        Evaluates receiver-centric cognitive bandwidth and emotional receptivity.
        """
        if not getattr(speaker, "is_alive", True) or not getattr(listener, "is_alive", True):
            return []

        cfg = self.get_channel_config(InformationChannelType.GOSSIP_AND_RUMORS)
        base_prob = float(cfg.get("diffusion_probability", 0.35))
        distort_rate = float(cfg.get("distortion_rate_per_hop", 0.05))

        speaker_ext = float(getattr(speaker, "personality", {}).get("extraversion", 0.5))
        listener_agree = float(getattr(listener, "personality", {}).get("agreeableness", 0.5))

        # Trust factor from directional opinion
        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        trust_mod = 0.0
        if op_eng and hasattr(op_eng, "get_net_opinion"):
            trust_mod = op_eng.get_net_opinion(listener.id, speaker.id) / 200.0

        speaker_known = self.npc_knowledge_ledger.get(speaker.id, set())
        listener_known = self.npc_knowledge_ledger.setdefault(listener.id, set())

        shareable = [
            self.active_items[i_id] for i_id in speaker_known
            if i_id in self.active_items and self.active_items[i_id].is_active
            and self.active_items[i_id].channel in (InformationChannelType.GOSSIP_AND_RUMORS, InformationChannelType.CIVIC_NOTICES)
            and i_id not in listener_known
            and not bool(self.active_items[i_id].payload.get("is_secret", False))
            and "SECRET_CLUB" not in self.active_items[i_id].topic
        ]

        transferred: List[InformationItem] = []
        for item in shareable[:3]:
            # Receiver-Centric Receptivity Check
            is_receptive, rec_mult = self.evaluate_receiver_receptivity(listener, item, context)
            if not is_receptive:
                continue

            diffusion_chance = max(0.10, min(0.95, (base_prob + (speaker_ext * 0.20) + trust_mod) * rec_mult + (listener_agree * 0.15)))
            if context.random.random() > diffusion_chance:
                continue

            # Clone with hop degradation
            new_distortion = min(1.0, item.distortion + distort_rate)
            new_credibility = max(0.10, item.credibility - (distort_rate * 0.8))
            item.hop_count += 1
            item.distortion = new_distortion
            item.credibility = new_credibility

            # Emotional relevance for listener
            emotional_rel = 1.0
            if item.subject_npc_id == listener.id:
                emotional_rel = 2.0  # It's about the listener!
            elif hasattr(listener, "social_profile") and listener.social_profile.get("spouse_id") == item.subject_npc_id:
                emotional_rel = 1.8  # About listener's spouse!

            self.record_learned_item(listener.id, item.item_id, current_tick, emotional_relevance=emotional_rel, credibility=new_credibility, distortion=new_distortion)
            transferred.append(item)
            self.total_rumors_diffused += 1

        return transferred

    # -------------------------------------------------------------------------
    # 3. CRIME & JUSTICE REPORTING (Citizens Reporting to Watch)
    # -------------------------------------------------------------------------
    def report_crime_to_watch(
        self,
        informant: NPC,
        guard: NPC,
        crime_topic: str,
        crime_description: str,
        suspect_id: Optional[str],
        incident_room_id: str,
        context: Any,
        current_tick: int
    ) -> InformationItem:
        """Citizen reports a witnessed theft, assault, or suspicious behavior directly to an on-duty guard."""
        cfg = self.get_channel_config(InformationChannelType.CRIME_AND_JUSTICE)
        vigilance_boost = float(cfg.get("vigilance_boost_per_report", 15.0))

        item = self.publish_item(
            channel=InformationChannelType.CRIME_AND_JUSTICE,
            topic=crime_topic,
            headline=f"Crime Report: {crime_topic} at {incident_room_id}",
            content=crime_description,
            source_npc_id=informant.id,
            subject_npc_id=suspect_id,
            target_location_id=incident_room_id,
            payload={
                "reported_by": informant.name,
                "received_by_guard": guard.name,
                "incident_room": incident_room_id,
                "vigilance_boost": vigilance_boost
            },
            current_tick=current_tick,
            context=context
        )

        # Informant and Guard record in memory
        self.record_learned_item(informant.id, item.item_id, current_tick, emotional_relevance=1.6)
        self.record_learned_item(guard.id, item.item_id, current_tick, emotional_relevance=1.8)

        # Guard increases alertness
        guard.adjust_feeling("vigilance" if "vigilance" in guard.feelings else "contentment", vigilance_boost)

        # Register formal judicial notice
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        guard.record_biographical_entry(
            current_tick, time_iso, "RECEIVED_CRIME_REPORT",
            f"Received official citizen crime report from {informant.name} regarding {crime_topic} at {incident_room_id}."
        )
        informant.record_biographical_entry(
            current_tick, time_iso, "REPORTED_CRIME",
            f"Reported {crime_topic} at {incident_room_id} to Watchman {guard.name}."
        )

        self.total_crimes_reported_to_watch += 1
        return item

    # -------------------------------------------------------------------------
    # 4. SHADOW INTELLIGENCE & WEALTHY MARK APPRAISALS (Underworld Network)
    # -------------------------------------------------------------------------
    def appraise_wealthy_mark(
        self,
        rogue: NPC,
        context: Any,
        current_tick: int
    ) -> Optional[InformationItem]:
        """
        Underworld informant appraises solvent citizens with substantial wealth,
        generating clandestine intelligence for thieves, burglars, and scavengers.
        """
        cfg = self.get_channel_config(InformationChannelType.SHADOW_INTELLIGENCE)
        min_wealth = float(cfg.get("wealthy_mark_threshold_gold", 50.0))
        allowed_kw = cfg.get("allowed_room_keywords", ["underworld", "vice", "tavern", "alley", "cellar", "shadow"])

        rogue_room = (rogue.location_id or "").lower()
        crime_prop = float(getattr(rogue, "vices", {}).get("crime_propensity", 0.0))
        if not any(k in rogue_room for k in allowed_kw) and crime_prop < 20.0:
            return None

        solvent_citizens = [
            n for n in context.npcs.values()
            if n.id != rogue.id and getattr(n, "is_alive", True) and float(getattr(n, "wealth", 0.0)) >= min_wealth
        ]
        if not solvent_citizens:
            return None

        solvent_citizens.sort(key=lambda n: getattr(n, "wealth", 0.0), reverse=True)
        target = solvent_citizens[0]
        mark_loc = target.work_location_id or target.home_location_id or target.location_id or (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")

        item = self.publish_item(
            channel=InformationChannelType.SHADOW_INTELLIGENCE,
            topic="WEALTHY_MARK_TARGET",
            headline=f"Clandestine Tip: {target.name} holds {target.wealth:.1f}g",
            content=f"Merchant {target.name} carries substantial gold reserves at {mark_loc}.",
            source_npc_id=rogue.id,
            subject_npc_id=target.id,
            target_location_id=mark_loc,
            payload={
                "target_id": target.id,
                "target_name": target.name,
                "appraised_wealth_gold": float(target.wealth),
                "target_location_id": mark_loc
            },
            current_tick=current_tick,
            context=context
        )

        self.record_learned_item(rogue.id, item.item_id, current_tick, emotional_relevance=1.7)
        self.total_shadow_marks_appraised += 1
        return item

    # -------------------------------------------------------------------------
    # 5. VOCATIONAL KNOWLEDGE & WORKSHOP MENTORSHIP
    # -------------------------------------------------------------------------
    def teach_vocational_skill(
        self,
        master: NPC,
        apprentice: NPC,
        skill_name: str,
        context: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """Master craftsman instructs an apprentice, transferring practical trade knowledge."""
        cfg = self.get_channel_config(InformationChannelType.VOCATIONAL_KNOWLEDGE)
        min_master_skill = float(cfg.get("master_skill_minimum", 50.0))
        transfer_rate = float(cfg.get("skill_transfer_rate", 0.50))
        max_gain = float(cfg.get("apprentice_skill_gain_max", 2.5))

        m_skill = master.get_skill(skill_name)
        if m_skill < min_master_skill:
            return {"success": False, "reason": "Teacher lacks master craftsman competence."}

        a_skill = apprentice.get_skill(skill_name)
        skill_delta = round(min(max_gain, max(0.5, (m_skill - a_skill) * 0.05 * transfer_rate)), 2)
        apprentice.skills[skill_name] = round(a_skill + skill_delta, 2)

        item = self.publish_item(
            channel=InformationChannelType.VOCATIONAL_KNOWLEDGE,
            topic=f"SKILL_{skill_name.upper()}",
            headline=f"Workshop Apprenticeship in {skill_name.title()}",
            content=f"{master.name} demonstrated advanced {skill_name} techniques to {apprentice.name}.",
            source_npc_id=master.id,
            subject_npc_id=apprentice.id,
            target_location_id=master.location_id,
            payload={
                "skill_name": skill_name,
                "master_skill": m_skill,
                "skill_gain": skill_delta,
                "new_apprentice_skill": apprentice.skills[skill_name]
            },
            current_tick=current_tick,
            context=context
        )

        self.record_learned_item(master.id, item.item_id, current_tick, emotional_relevance=1.4)
        self.record_learned_item(apprentice.id, item.item_id, current_tick, emotional_relevance=1.8)

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        apprentice.record_biographical_entry(
            current_tick, time_iso, "VOCATIONAL_STUDY",
            f"Studied under Master {master.name}, improving {skill_name} by +{skill_delta:.2f} (now {apprentice.skills[skill_name]:.1f})."
        )
        self.total_vocational_lessons += 1

        return {
            "success": True,
            "skill_name": skill_name,
            "skill_gain": skill_delta,
            "new_skill_level": apprentice.skills[skill_name]
        }

    # -------------------------------------------------------------------------
    # AMBIENT WAVE PERCEPTION
    # -------------------------------------------------------------------------
    def process_ambient_wave_perception(self, context: Any, current_tick: int) -> int:
        """
        Processes ambient spatial waves in the environment.
        Co-located agents passively perceive waves based on cognitive bandwidth and room presence.
        """
        # 1. Clean expired waves
        self.active_waves = [w for w in self.active_waves if (current_tick - w.created_tick) < w.duration_ticks]

        if not hasattr(context, "npcs") or not context.npcs or not self.active_waves:
            return 0

        perceptions_count = 0
        for wave in self.active_waves:
            item = self.active_items.get(wave.item_id)
            if not item or not item.is_active:
                continue

            # Find citizens in the wave's room
            occupants = [n for n in context.npcs.values() if n.location_id == wave.current_room_id and getattr(n, "is_alive", True)]
            for occupant in occupants:
                known_set = self.npc_knowledge_ledger.setdefault(occupant.id, set())
                if item.item_id in known_set:
                    continue  # Already knows

                is_receptive, rec_mult = self.evaluate_receiver_receptivity(occupant, item, context)
                if not is_receptive:
                    continue

                perception_prob = max(0.05, min(0.95, wave.intensity * rec_mult))
                if context.random.random() < perception_prob:
                    self.record_learned_item(occupant.id, item.item_id, current_tick, emotional_relevance=1.0, credibility=item.credibility)
                    perceptions_count += 1
                    self.total_ambient_perceptions += 1

        return perceptions_count

    # -------------------------------------------------------------------------
    # LIFECYCLE & AMBIENT DIFFUSION
    # -------------------------------------------------------------------------
    def process_lifecycle_and_ambient_diffusion(self, context: Any, current_tick: int) -> None:
        """
        Hourly processing called by the UnifiedInformationSubsystem:
        1. Expire outdated information items.
        2. Evict decayed memories (Borchert memory half-life) to maintain O(1) memory bound.
        3. Process ambient spatial wave perception across rooms.
        4. Diffuse word-of-mouth gossip between co-located citizens in social spaces.
        5. Autonomously read notice boards for citizens in circulation plazas.
        """
        # 1. Expire old items
        for i_id in list(self.active_items.keys()):
            item = self.active_items[i_id]
            if current_tick >= item.expires_tick:
                item.is_active = False
                self.item_history.append(item)
                del self.active_items[i_id]

        # 2. Epistemic memory forgetting & salience eviction
        self.evict_decayed_memories(current_tick)

        if not hasattr(context, "npcs") or not context.npcs:
            return

        # 3. Ambient wave perception
        self.process_ambient_wave_perception(context, current_tick)

        # 4. Room-based social gossip and notice board reading
        rooms_occupancy: Dict[str, List[NPC]] = {}
        for npc in context.npcs.values():
            if getattr(npc, "is_alive", True) and npc.location_id:
                rooms_occupancy.setdefault(npc.location_id, []).append(npc)

        for room_id, occupants in rooms_occupancy.items():
            r_low = room_id.lower()

            # a. Notice boards in civic circulation hubs
            if any(k in r_low for k in ("square", "hall", "plaza", "market")):
                for citizen in occupants:
                    cons = float(getattr(citizen, "personality", {}).get("conscientiousness", 0.5))
                    if context.random.random() < (0.25 + cons * 0.30):
                        self.read_notice_board(citizen, room_id, context, current_tick)

            # b. Social gossip between co-located pairs in gathering hubs
            if len(occupants) >= 2 and any(k in r_low for k in ("tavern", "square", "plaza", "workshop", "bakery", "hall", "inn")):
                shuffled = list(occupants)
                context.random.shuffle(shuffled)
                for i in range(0, len(shuffled) - 1, 2):
                    self.share_gossip(shuffled[i], shuffled[i+1], context, current_tick)
                    self.share_gossip(shuffled[i+1], shuffled[i], context, current_tick)
