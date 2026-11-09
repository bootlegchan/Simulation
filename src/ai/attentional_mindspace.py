"""
Attentional Mindspace & Thinking Ability Engine.
Operates 100% on declarative configurations from data/settings/attentional_mindspace.json.
Models dynamic cognitive stream of consciousness:
1. Configurable thinking ability profiles per NPC (Scholar, Focused Craftsman, Impulsive, Scatterbrain).
2. Continuous attentional weighting of thoughts, memories, and somatic appetites based on personality, state, and distractibility.
3. Conscious attentional spotlight bounded by individual working memory capacity.
4. Bidirectional utility bias injection into multinomial logit deliberation without implicit state machines.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry


@dataclass
class ThoughtItem:
    domain: str
    title: str
    content: str
    base_salience: float = 1.0
    attentional_score: float = 1.0
    target_entity_id: Optional[str] = None
    target_location_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    utility_biases: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "title": self.title,
            "content": self.content,
            "base_salience": round(self.base_salience, 3),
            "attentional_score": round(self.attentional_score, 3),
            "target_entity_id": self.target_entity_id,
            "target_location_id": self.target_location_id,
            "tags": self.tags,
            "utility_biases": {k: round(v, 2) for k, v in self.utility_biases.items()},
            "metadata": self.metadata
        }


@dataclass
class ThinkingAbilityProfile:
    profile_id: str
    name: str
    working_memory_capacity: int = 4
    focus_depth: float = 1.0
    distractibility: float = 0.45
    deliberation_bandwidth: float = 1.0
    emotional_reactivity: float = 1.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "working_memory_capacity": self.working_memory_capacity,
            "focus_depth": round(self.focus_depth, 2),
            "distractibility": round(self.distractibility, 2),
            "deliberation_bandwidth": round(self.deliberation_bandwidth, 2),
            "emotional_reactivity": round(self.emotional_reactivity, 2),
            "description": self.description
        }


class AttentionalMindspaceEngine:
    """
    Central Attentional Mindspace Engine.
    Dynamically weighs competing mental streams (work, somatic appetite, romance/crush,
    anxiety/grudges, leisure) based on configurable thinking ability and continuous psychological state.
    """
    _instance: Optional["AttentionalMindspaceEngine"] = None

    @classmethod
    def get_instance(cls) -> "AttentionalMindspaceEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.thinking_profiles: Dict[str, ThinkingAbilityProfile] = {}
        # npc_id -> List[ThoughtItem] (active conscious spotlight)
        self.active_spotlights: Dict[str, List[ThoughtItem]] = {}
        # npc_id -> ThoughtItem (dominant winning thought)
        self.dominant_thoughts: Dict[str, ThoughtItem] = {}
        # Statistics
        self.total_evaluations_count: int = 0
        self.total_spotlight_transitions: int = 0
        self._load_from_settings()

    def clear(self) -> None:
        self.active_spotlights.clear()
        self.dominant_thoughts.clear()
        self.total_evaluations_count = 0
        self.total_spotlight_transitions = 0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        cfg = SettingsRegistry.get_instance().get("attentional_mindspace")
        mind_cfg = cfg.get("attentional_mindspace", {})
        prof_defs = mind_cfg.get("thinking_ability_profiles", {})
        self.thinking_profiles.clear()

        for p_id, data in prof_defs.items():
            self.thinking_profiles[p_id] = ThinkingAbilityProfile(
                profile_id=p_id,
                name=data.get("name", p_id),
                working_memory_capacity=int(data.get("working_memory_capacity", 4)),
                focus_depth=float(data.get("focus_depth", 1.0)),
                distractibility=float(data.get("distractibility", 0.45)),
                deliberation_bandwidth=float(data.get("deliberation_bandwidth", 1.0)),
                emotional_reactivity=float(data.get("emotional_reactivity", 1.0)),
                description=data.get("description", "")
            )

    def get_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("attentional_mindspace").get("attentional_mindspace", {})

    def resolve_thinking_profile(self, npc: Any) -> ThinkingAbilityProfile:
        """
        Resolves an NPC's thinking ability profile:
        1. Explicit profile ID declared on npc.cognition
        2. Configurable direct numerical overrides on npc.cognition
        3. Heuristic resolution from vocation, personality, and intelligence
        """
        cog = getattr(npc, "cognition", {}) or {}
        p_id = cog.get("thinking_profile")

        # Heuristic resolution if not explicitly declared
        if not p_id:
            occ = (getattr(npc, "occupation", "") or "").lower()
            p = getattr(npc, "personality", {}) or {}
            cons = float(p.get("conscientiousness", 0.5))
            ext = float(p.get("extraversion", 0.5))
            vices = getattr(npc, "vices", {}) or {}
            crime_prop = float(vices.get("crime_propensity", 0.0))

            if any(k in occ for k in ("notary", "clerk", "mayor", "magistrate", "priest")):
                p_id = "SCHOLAR_ANALYTICAL"
            elif any(k in occ for k in ("smith", "blacksmith", "carpenter", "baker", "miller", "weaver", "mason")):
                p_id = "FOCUSED_CRAFTSMAN"
            elif crime_prop >= 40.0 or float(vices.get("gambling_drive", 0.0)) >= 30.0:
                p_id = "INTUITIVE_IMPULSIVE"
            elif cons < 0.35 and ext > 0.60:
                p_id = "SCATTERBRAIN_ABSENTMINDED"
            else:
                p_id = "BALANCED_COMMONER"

        base_prof = self.thinking_profiles.get(p_id, self.thinking_profiles.get("BALANCED_COMMONER", ThinkingAbilityProfile("BALANCED_COMMONER", "Balanced Commoner")))

        # Apply configurable direct overrides from npc.cognition
        cap = int(cog.get("working_memory_capacity", base_prof.working_memory_capacity))
        depth = float(cog.get("focus_depth", base_prof.focus_depth))
        distract = float(cog.get("distractibility", base_prof.distractibility))
        bandwidth = float(cog.get("deliberation_bandwidth", base_prof.deliberation_bandwidth))
        react = float(cog.get("emotional_reactivity", base_prof.emotional_reactivity))

        return ThinkingAbilityProfile(
            profile_id=p_id,
            name=base_prof.name,
            working_memory_capacity=max(1, min(9, cap)),
            focus_depth=max(0.2, min(2.5, depth)),
            distractibility=max(0.05, min(1.0, distract)),
            deliberation_bandwidth=max(0.3, min(2.0, bandwidth)),
            emotional_reactivity=max(0.3, min(2.5, react)),
            description=base_prof.description
        )

    def generate_candidate_thoughts(self, npc: Any, context: Any, current_tick: int) -> List[ThoughtItem]:
        """
        Synthesizes candidate mental thoughts competing for conscious spotlight:
        - Somatic Appetites (hunger, bakery/tavern cravings)
        - Somatic Rest (fatigue, sleep pressure)
        - Vocational Labor & Crafting
        - Romantic Longing & Crushes
        - Community Leisure & Games
        - Anxiety, Debts & Grudges
        - Epistemic Working Memory Traces (books, clues, secrets)
        """
        candidates: List[ThoughtItem] = []
        cfg = self.get_config()
        domains = cfg.get("thought_domains", {})

        needs = getattr(npc, "needs", {}) or {}
        feelings = getattr(npc, "feelings", {}) or {}
        p = getattr(npc, "personality", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}
        vices = getattr(npc, "vices", {}) or {}

        hunger = float(needs.get("hunger", 0.0))
        energy = float(needs.get("energy", 100.0))
        fatigue = max(0.0, 100.0 - energy)
        stress = float(feelings.get("stress", 0.0))
        passion = float(feelings.get("passion", 0.0))
        resentment = float(feelings.get("resentment", 0.0))
        guilt = float(feelings.get("guilt", 0.0))
        wealth = float(getattr(npc, "wealth", 50.0))
        occ = (getattr(npc, "occupation", "") or "").lower()

        # -------------------------------------------------------------
        # 1. SOMATIC APPETITE STREAM
        # -------------------------------------------------------------
        if hunger > 15.0 and "SOMATIC_APPETITE" in domains:
            d_spec = domains["SOMATIC_APPETITE"]
            exp_f = float(d_spec.get("state_amplifiers", {}).get("hunger_exponential_factor", 1.75))
            raw_saliency = ((hunger / 25.0) ** exp_f) * 0.08
            candidates.append(ThoughtItem(
                domain="SOMATIC_APPETITE",
                title="Hunger & Appetite",
                content="Stomach rumbling with thoughts of fresh bread or tavern stew.",
                base_salience=min(1.0, max(0.1, raw_saliency)),
                tags=["food", "bread", "hunger", "meal"],
                utility_biases=dict(d_spec.get("utility_biases", {}))
            ))

        # -------------------------------------------------------------
        # 2. SOMATIC REST STREAM
        # -------------------------------------------------------------
        if fatigue > 25.0 and "SOMATIC_REST" in domains:
            d_spec = domains["SOMATIC_REST"]
            exp_f = float(d_spec.get("state_amplifiers", {}).get("fatigue_exponential_factor", 1.6))
            raw_saliency = ((fatigue / 25.0) ** exp_f) * 0.07
            candidates.append(ThoughtItem(
                domain="SOMATIC_REST",
                title="Bodily Fatigue",
                content="Weary bones aching for the comfort of rest in a warm bed.",
                base_salience=min(1.0, max(0.1, raw_saliency)),
                tags=["rest", "sleep", "fatigue"],
                utility_biases=dict(d_spec.get("utility_biases", {}))
            ))

        # -------------------------------------------------------------
        # 3. VOCATIONAL LABOR STREAM
        # -------------------------------------------------------------
        if "VOCATIONAL_LABOR" in domains:
            d_spec = domains["VOCATIONAL_LABOR"]
            cons = float(p.get("conscientiousness", 0.5))
            amb = float(getattr(npc, "mental_attributes", {}).get("ambition", 50.0)) / 100.0

            # Check if within shift
            hour = (current_tick // 60) % 24
            if hasattr(context, "clock") and hasattr(context.clock, "current_virtual_time"):
                vt = context.clock.current_virtual_time
                hour = vt.hour + vt.minute / 60.0

            from src.entities.occupations import OccupationRegistry
            occ_reg = OccupationRegistry.get_instance()
            shift = occ_reg.get_shift_window(getattr(npc, "occupation", ""))
            in_shift = shift.is_within_shift(hour)

            if in_shift:
                shift_sal = 0.50
            else:
                hours_before = (shift.base_start_hour - hour) % 24.0
                if 0.0 < hours_before <= 1.5:
                    shift_sal = 0.20
                else:
                    shift_sal = 0.05
            base_sal = (cons * 0.40) + (amb * 0.30) + shift_sal
            candidates.append(ThoughtItem(
                domain="VOCATIONAL_LABOR",
                title=f"Vocational Duty ({shift.shift_name.title()})",
                content=f"Concentrating on duties as {npc.occupation} and workshop orders.",
                base_salience=min(1.0, max(0.1, base_sal)),
                tags=["work", "craft", "production", "order", "farming", "harvest"],
                utility_biases=dict(d_spec.get("utility_biases", {}))
            ))

            volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
            if volition_eng and npc.id in volition_eng.aspirations:
                asp = volition_eng.aspirations[npc.id]
                candidates.append(ThoughtItem(
                    domain="VOCATIONAL_LABOR",
                    title=f"Career Aspiration: {asp.target_occupation}",
                    content=f"Driven to improve {asp.required_skill} (currently {asp.current_level:.1f}/{asp.required_level:.1f}) to qualify as {asp.target_occupation}.",
                    base_salience=min(1.0, max(0.2, 0.45 + (amb * 0.35) + (cons * 0.20))),
                    tags=["career", "aspiration", "study", "vocational"],
                    utility_biases={"work_production": 35.0, "socialize": -15.0}
                ))

        # -------------------------------------------------------------
        # 4. ROMANCE & CRUSH STREAM (Grounded in real partners/crushes)
        # -------------------------------------------------------------
        spouse_id = sp.get("spouse_id") or sp.get("partner_id")
        target_partner = context.npcs.get(spouse_id) if (spouse_id and hasattr(context, "npcs")) else None
        tension = float(getattr(npc, "unmet_intimacy_tension", 0.0))

        rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else None
        crush_partner = None
        if not target_partner and rom_eng and hasattr(rom_eng, "bonds"):
            for b_key, bond in rom_eng.bonds.items():
                if npc.id in (bond.initiator_id, bond.target_id):
                    cand_id = bond.target_id if bond.initiator_id == npc.id else bond.initiator_id
                    if (bond.romantic_affection >= 30.0 or bond.physical_attraction >= 40.0) and hasattr(context, "npcs") and cand_id in context.npcs:
                        crush_partner = context.npcs[cand_id]
                        break

        actual_partner = target_partner or crush_partner
        if actual_partner and "ROMANCE_AND_CRUSH" in domains:
            d_spec = domains["ROMANCE_AND_CRUSH"]
            p_name = actual_partner.name
            raw_sal = (passion / 100.0 * 0.50) + (tension / 100.0 * 0.40) + (float(p.get("extraversion", 0.5)) * 0.20)
            candidates.append(ThoughtItem(
                domain="ROMANCE_AND_CRUSH",
                title=f"Affection for {p_name}",
                content=f"Thoughts drift tenderly to {p_name}, longing for shared private moments.",
                base_salience=min(1.0, max(0.1, raw_sal)),
                target_entity_id=actual_partner.id,
                tags=["love", "romance", "crush", "intimacy"],
                utility_biases=dict(d_spec.get("utility_biases", {}))
            ))
        elif not actual_partner and (tension > 35.0 or float(feelings.get("loneliness", 0.0)) > 25.0):
            # Unattached single: general longing for companionship, not fixating on a phantom lover
            candidates.append(ThoughtItem(
                domain="LOVE_BELONGING",
                title="Romantic Longing & Courtship Ambition",
                content="Feeling unattached and hoping to meet an attractive companion at the square or tavern.",
                base_salience=min(0.40, max(0.1, (tension / 100.0 * 0.25) + (float(feelings.get("loneliness", 0.0)) / 100.0 * 0.25))),
                target_entity_id=None,
                tags=["social", "courtship", "dating", "loneliness"],
                utility_biases={"socialize": 15.0}
            ))

        # -------------------------------------------------------------
        # 5. ANXIETY, DEBTS & GRUDGES STREAM
        # -------------------------------------------------------------
        if (stress > 25.0 or resentment > 20.0 or guilt > 20.0 or wealth < 8.0) and "ANXIETY_AND_GRUDGE" in domains:
            d_spec = domains["ANXIETY_AND_GRUDGE"]
            neuro = float(p.get("neuroticism", 0.5))
            raw_sal = (stress / 100.0 * 0.35) + (resentment / 100.0 * 0.30) + (guilt / 100.0 * 0.25) + (neuro * 0.25)
            if wealth < 8.0:
                raw_sal += 0.30
            if guilt > 20.0:
                candidates.append(ThoughtItem(
                    domain="ANXIETY_AND_GRUDGE",
                    title="Moral Remorse & Guilt",
                    content="Inner guilt brooding over transgressive acts; longing for spiritual absolution.",
                    base_salience=min(1.0, max(0.2, (guilt / 100.0 * 0.70) + (neuro * 0.20))),
                    tags=["guilt", "remorse", "confession", "moral"],
                    utility_biases={"socialize": 25.0, "rest": -10.0}
                ))
            else:
                candidates.append(ThoughtItem(
                    domain="ANXIETY_AND_GRUDGE",
                    title="Anxiety & Unsettled Grievances",
                    content="Inner tension brooding over financial shortages, debts, and slights.",
                    base_salience=min(1.0, max(0.1, raw_sal)),
                    tags=["anxiety", "grudge", "debt", "stress"],
                    utility_biases=dict(d_spec.get("utility_biases", {}))
                ))

        # -------------------------------------------------------------
        # 6. COMMUNITY LEISURE STREAM
        # -------------------------------------------------------------
        hour = (current_tick // 60) % 24
        if hasattr(context, "clock") and hasattr(context.clock, "current_virtual_time"):
            hour = context.clock.current_virtual_time.hour
        is_evening = (17 <= hour <= 23)

        if (is_evening or float(vices.get("gambling_drive", 0.0)) > 25.0) and "COMMUNITY_LEISURE" in domains:
            d_spec = domains["COMMUNITY_LEISURE"]
            ext = float(p.get("extraversion", 0.5))
            gamb = float(vices.get("gambling_drive", 0.0)) / 100.0
            raw_sal = (ext * 0.40) + (gamb * 0.35) + (0.30 if is_evening else 0.0)
            candidates.append(ThoughtItem(
                domain="COMMUNITY_LEISURE",
                title="Tavern Fellowship & Games",
                content="Eager for friendly banter, lawn bowls, or dice hazard at the tavern.",
                base_salience=min(1.0, max(0.1, raw_sal)),
                tags=["leisure", "game", "dice", "fellowship"],
                utility_biases=dict(d_spec.get("utility_biases", {}))
            ))

        # -------------------------------------------------------------
        # 7. EPISTEMIC KNOWLEDGE ATOMS IN ACTIVE MEMORY
        # -------------------------------------------------------------
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
        if ep_eng and hasattr(ep_eng, "get_active_working_memory"):
            active_traces = ep_eng.get_active_working_memory(npc, current_tick)
            for trace in active_traces[:3]:
                # Skip pure spatial landmark facts from competing as intrusive thoughts
                if "landmark" in trace.atom.tags or "spatial" in trace.atom.tags:
                    continue

                domain = "EPISTEMIC_RECORD"
                if any(t in trace.atom.tags for t in ("love", "spouse", "romance")):
                    domain = "ROMANCE_AND_CRUSH"
                elif any(t in trace.atom.tags for t in ("work", "craft", "recipe", "farming")):
                    domain = "VOCATIONAL_LABOR"
                elif any(t in trace.atom.tags for t in ("crime", "clue", "suspect", "grudge")):
                    domain = "ANXIETY_AND_GRUDGE"

                candidates.append(ThoughtItem(
                    domain=domain,
                    title=trace.atom.title,
                    content=trace.atom.content,
                    base_salience=trace.salience * (trace.atom.emotional_relevance / 2.0),
                    target_entity_id=trace.atom.subject_id or trace.atom.actor_id,
                    target_location_id=trace.atom.location_id,
                    tags=list(trace.atom.tags),
                    utility_biases={}
                ))

        return candidates

    def evaluate_attentional_mindspace(
        self,
        npc: Any,
        context: Any,
        current_tick: int
    ) -> Dict[str, Any]:
        """
        Evaluates the NPC's conscious stream of consciousness:
        1. Resolves individual configurable ThinkingAbilityProfile.
        2. Synthesizes candidate thoughts across all mental streams.
        3. Dynamically weighs attentional scores based on state, personality, focus depth, and distractibility.
        4. Bounds conscious spotlight to working_memory_capacity (K items).
        5. Selects top winning thought as dominant_thought.
        6. Extracts continuous utility biases for downstream logit sampling.
        """
        profile = self.resolve_thinking_profile(npc)
        candidates = self.generate_candidate_thoughts(npc, context, current_tick)
        cfg = self.get_config()
        domains = cfg.get("thought_domains", {})
        injection_scale = float(cfg.get("mindspace_dynamics", {}).get("utility_injection_scale", 0.75))

        needs = getattr(npc, "needs", {}) or {}
        feelings = getattr(npc, "feelings", {}) or {}
        p = getattr(npc, "personality", {}) or {}

        hunger = float(needs.get("hunger", 0.0))
        fatigue = max(0.0, 100.0 - float(needs.get("energy", 100.0)))
        stress = float(feelings.get("stress", 0.0))
        passion = float(feelings.get("passion", 0.0))
        tension = float(getattr(npc, "unmet_intimacy_tension", 0.0))

        # Dynamically calculate Attentional Weight (A_i) for each candidate thought
        for thought in candidates:
            domain_spec = domains.get(thought.domain, {})
            score = thought.base_salience

            # State amplifiers and inhibitors
            if thought.domain == "SOMATIC_APPETITE":
                hunger_boost = 1.0 + ((hunger / 25.0) ** 1.6) * 0.40 * profile.emotional_reactivity
                distract_boost = 1.0 + (profile.distractibility * 0.50)
                score *= (hunger_boost * distract_boost)

            elif thought.domain == "SOMATIC_REST":
                fatigue_boost = 1.0 + ((fatigue / 25.0) ** 1.5) * 0.35
                score *= fatigue_boost

            elif thought.domain == "ROMANCE_AND_CRUSH":
                passion_boost = 1.0 + (passion * 0.02 * profile.emotional_reactivity) + (tension * 0.015)
                score *= (passion_boost * profile.focus_depth)

            elif thought.domain == "VOCATIONAL_LABOR":
                cons = float(p.get("conscientiousness", 0.5))
                work_focus = 1.0 + (cons * 0.60) * profile.focus_depth
                # Hunger / Fatigue inhibits vocational focus
                drag = 1.0 - min(0.60, (hunger * 0.006) + (fatigue * 0.005))
                score *= (work_focus * drag)

            elif thought.domain == "ANXIETY_AND_GRUDGE":
                neuro = float(p.get("neuroticism", 0.5))
                anxiety_boost = 1.0 + (stress * 0.025 * profile.emotional_reactivity) + (neuro * 0.50)
                score *= anxiety_boost

            elif thought.domain == "COMMUNITY_LEISURE":
                ext = float(p.get("extraversion", 0.5))
                leisure_boost = 1.0 + (ext * 0.40) + (profile.distractibility * 0.30)
                score *= leisure_boost

            thought.attentional_score = max(0.01, round(score, 3))

        # Sort candidate thoughts by attentional score descending
        candidates.sort(key=lambda t: t.attentional_score, reverse=True)

        # Bounded strictly to configurable working memory capacity (K items)
        capacity = profile.working_memory_capacity
        spotlight = candidates[:capacity]
        self.active_spotlights[npc.id] = spotlight

        dominant = spotlight[0] if spotlight else ThoughtItem("IDLE", "Calm Mind", "Mind at rest with quiet awareness.")
        prev_dominant = self.dominant_thoughts.get(npc.id)
        if not prev_dominant or prev_dominant.domain != dominant.domain:
            self.total_spotlight_transitions += 1
        self.dominant_thoughts[npc.id] = dominant

        # Store in character inner thought history on NPC
        if not hasattr(npc, "thought_history"):
            npc.thought_history = []
        npc.active_thoughts = [t.to_dict() for t in spotlight]
        npc.dominant_thought = dominant.to_dict()

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        record = {
            "tick": current_tick,
            "time_iso": time_iso,
            "domain": dominant.domain,
            "title": dominant.title,
            "content": dominant.content,
            "attentional_score": dominant.attentional_score
        }
        npc.thought_history.append(record)
        if len(npc.thought_history) > 5:
            npc.thought_history = npc.thought_history[-5:]

        # Calculate continuous utility biases injected into UtilityEvaluator
        utility_biases: Dict[str, float] = {}
        for t in spotlight:
            weight = min(1.5, t.attentional_score) * (1.0 / math.sqrt(capacity)) * injection_scale
            for drive_name, base_bias in t.utility_biases.items():
                utility_biases[drive_name] = utility_biases.get(drive_name, 0.0) + (base_bias * weight)

        self.total_evaluations_count += 1
        return {
            "thinking_profile": profile.to_dict(),
            "dominant_thought": dominant.to_dict(),
            "spotlight_count": len(spotlight),
            "spotlight_thoughts": [t.to_dict() for t in spotlight],
            "utility_biases": {k: round(v, 2) for k, v in utility_biases.items()}
        }
