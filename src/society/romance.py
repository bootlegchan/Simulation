"""Romance, Marriage, Dyadic Consent, and Relationship Stage Registry."""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple

from src.society.information_networks import InformationChannelType, WaveMedium
class RelationshipStage(str, Enum):
    STRANGER = "STRANGER"
    ACQUAINTANCE = "ACQUAINTANCE"
    FRIEND = "FRIEND"
    CLOSE_FRIEND = "CLOSE_FRIEND"
    CRUSH = "CRUSH"
    COURTING = "COURTING"
    LOVERS = "LOVERS"
    BETROTHED = "BETROTHED"
    SPOUSES = "SPOUSES"
    RIVALS = "RIVALS"
    ESTRANGED = "ESTRANGED"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

class AgreementType(Enum):
    MONOGAMOUS_EXCLUSIVE = "MONOGAMOUS_EXCLUSIVE"
    OPEN_POLYAMOROUS = "OPEN_POLYAMOROUS"
    QUEERPLATONIC_DEVOTION = "QUEERPLATONIC_DEVOTION"

class AffectionStyle(Enum):
    WORDS_OF_AFFIRMATION = "WORDS_OF_AFFIRMATION"
    QUALITY_TIME = "QUALITY_TIME"
    RECEIVING_GIFTS = "RECEIVING_GIFTS"
    PHYSICAL_TOUCH = "PHYSICAL_TOUCH"

@dataclass
class RelationshipStageDefinition:
    stage_id: str
    name: str
    tier: int = 1
    min_romantic_affection: float = 0.0
    min_trust: float = 0.0

@dataclass
class InterpersonalBond:
    initiator_id: str
    target_id: str
    stage: RelationshipStage = RelationshipStage.ACQUAINTANCE
    romantic_affection: float = 10.0
    trust: float = 50.0
    respect: float = 50.0
    physical_attraction: float = 20.0
    agreement_type: AgreementType = AgreementType.MONOGAMOUS_EXCLUSIVE
    declared_boundaries: List[str] = field(default_factory=list)

    def calculate_continuous_chemistry(self, actor_energy: float = 100.0, actor_stress: float = 0.0) -> float:
        """
        Continuous Dyadic Chemistry Potential:
        Φ_intimacy = (w_attract * Attraction + w_affect * Affection + w_trust * Trust) * Stamina - StressPenalty
        """
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        chem_cfg = rom_cfg.get("relationship_chemistry", {})

        w_attr = float(chem_cfg.get("physical_attraction_weight", 0.35))
        w_aff = float(chem_cfg.get("romantic_affection_weight", 0.35))
        w_tr = float(chem_cfg.get("trust_weight", 0.30))
        stamina_min = float(chem_cfg.get("stamina_factor_min", 0.20))
        stress_inhibit = float(chem_cfg.get("stress_inhibition_factor", 0.50))

        stamina_factor = max(stamina_min, actor_energy / 100.0)
        raw_affinity = (w_attr * self.physical_attraction) + (w_aff * self.romantic_affection) + (w_tr * self.trust)
        chem = (raw_affinity * stamina_factor) - (actor_stress * stress_inhibit)
        return round(chem, 2)

    def discuss_boundaries(self, agreement: AgreementType, boundaries: List[str]) -> Dict[str, Any]:
        self.agreement_type = agreement
        self.declared_boundaries = list(boundaries)
        return {"success": True}

class RelationshipStageRegistry:
    _instance: Optional["RelationshipStageRegistry"] = None

    @classmethod
    def get_instance(cls) -> "RelationshipStageRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        stage_defs = rom_cfg.get("stage_definitions", {})

        self.stages: Dict[str, RelationshipStageDefinition] = {}
        for s in RelationshipStage:
            spec = stage_defs.get(s.value, {})
            self.stages[s.value] = RelationshipStageDefinition(
                stage_id=s.value,
                name=s.value.title(),
                tier=int(spec.get("tier", 1)),
                min_romantic_affection=float(spec.get("min_affection", 0.0)),
                min_trust=float(spec.get("min_trust", 0.0))
            )

    def register_stage(self, definition: RelationshipStageDefinition) -> None:
        self.stages[definition.stage_id.upper()] = definition

class RomanceEngine:
    def __init__(self, decision_engine: Any = None, config: Optional[Dict[str, Any]] = None):
        self.bonds: Dict[str, InterpersonalBond] = {}
        self.jealousy_triggers_count: int = 0
        self.total_intimacy_acts: int = 0
        self.total_intimacy_rejections: int = 0
        self.total_scandals_emitted: int = 0

    def get_or_create_bond(self, id_a: str, id_b: str, context: Optional[Any] = None) -> InterpersonalBond:
        k = tuple(sorted([id_a, id_b]))
        bond_key = f"{k[0]}:{k[1]}"
        if bond_key not in self.bonds:
            bond = InterpersonalBond(initiator_id=id_a, target_id=id_b)
            if context and hasattr(context, "npcs"):
                npc_a = context.npcs.get(id_a)
                npc_b = context.npcs.get(id_b)
                if npc_a and npc_b:
                    sp_a = getattr(npc_a, "social_profile", {}) or {}
                    sp_b = getattr(npc_b, "social_profile", {}) or {}
                    if sp_a.get("spouse_id") == id_b or sp_b.get("spouse_id") == id_a:
                        bond.stage = RelationshipStage.SPOUSES
                        bond.romantic_affection = 75.0
                        bond.physical_attraction = 70.0
                        bond.trust = 80.0
                    elif sp_a.get("partner_id") == id_b or sp_b.get("partner_id") == id_a:
                        bond.stage = RelationshipStage.BETROTHED
                        bond.romantic_affection = 65.0
                        bond.physical_attraction = 65.0
                        bond.trust = 70.0
            self.bonds[bond_key] = bond
        return self.bonds[bond_key]

    def get_romantic_partner(self, npc_id: str, npcs: Dict[str, Any]) -> Optional[Tuple[Any, InterpersonalBond]]:
        for k, bond in self.bonds.items():
            if bond.stage in (RelationshipStage.LOVERS, RelationshipStage.BETROTHED, RelationshipStage.SPOUSES):
                if bond.initiator_id == npc_id and bond.target_id in npcs:
                    return (npcs[bond.target_id], bond)
                elif bond.target_id == npc_id and bond.initiator_id in npcs:
                    return (npcs[bond.initiator_id], bond)
        return None

    def calculate_public_intimacy_willingness(
        self,
        npc: Any,
        witnesses_count: int,
        is_private_room: bool,
        bond: Optional[InterpersonalBond] = None
    ) -> Tuple[bool, float, str]:
        """
        Calculates an NPC's elastic willingness for intimacy in the current space.
        Never locks off public areas: elastic trade-off between romantic pull,
        exhibitionism, intoxication, and modesty restraint.
        """
        if is_private_room and witnesses_count == 0:
            return True, 100.0, "Private sanctuary"

        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        priv_cfg = rom_cfg.get("elastic_privacy_and_exhibitionism", rom_cfg.get("privacy_and_space", {}))

        base_inhibition = float(priv_cfg.get("base_public_inhibition", 25.0)) if not is_private_room else 0.0
        # Crowd exposure pressure caps gracefully so large markets don't create infinite resistance
        max_witness_inhibit = float(priv_cfg.get("max_witness_inhibition_cap", 30.0))
        witness_inhibition = min(max_witness_inhibit, float(priv_cfg.get("witness_inhibition_weight", 6.0)) * witnesses_count)
        exposure_pressure = base_inhibition + witness_inhibition

        vices = getattr(npc, "vices", {}) or {}
        p = getattr(npc, "personality", {}) or {}
        feelings = getattr(npc, "feelings", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}
        tags = getattr(npc, "tags", set()) or set()

        exhibitionism = float(vices.get("exhibitionism", 0.0))
        thrill_seeking = float(vices.get("thrill_seeking", 0.0))
        alcohol = float(vices.get("alcohol_dependence", 0.0))
        passion = float(feelings.get("passion", 0.0))
        openness = float(p.get("openness", 0.5))
        cons = float(p.get("conscientiousness", 0.5))
        honor = float(sp.get("moral_values", {}).get("honor", 0.5))

        attraction = float(bond.physical_attraction if bond else 20.0)
        affection = float(bond.romantic_affection if bond else 10.0)

        # 1. Romantic & Somatic Attraction Pull
        romantic_pull = (attraction * 0.40) + (affection * 0.30) + (passion * 0.40)

        # 2. Exhibitionist / Thrill-Seeking Affinity
        tag_bonus = 0.0
        if "TAG_EXHIBITIONIST" in tags or "exhibitionist" in str(tags).lower():
            tag_bonus += 50.0
        if "TAG_THRILL_SEEKER" in tags or "thrill_seeker" in str(tags).lower():
            tag_bonus += 30.0
        if "TAG_HEDONIST" in tags:
            tag_bonus += 25.0

        w_exh = float(priv_cfg.get("exhibitionism_affinity_weight", 1.50))
        w_thrill = float(priv_cfg.get("thrill_seeking_affinity_weight", 1.00))
        w_open = float(priv_cfg.get("openness_bonus_weight", 15.0))
        exhibitionist_affinity = (exhibitionism * w_exh) + (thrill_seeking * w_thrill) + (openness * w_open) + tag_bonus

        # 3. Modesty Restraint (mitigated by alcohol and passion)
        alc_reduct = float(priv_cfg.get("alcohol_inhibition_reduction", 0.50))
        modesty_inhibition = max(0.0, (cons * 20.0) + (honor * 15.0) - (alcohol * alc_reduct) - (passion * 0.30))

        net_willingness = romantic_pull + exhibitionist_affinity - modesty_inhibition

        # Overwhelming passion overrides modesty
        overwhelming_thresh = float(priv_cfg.get("overwhelming_passion_threshold", 70.0))
        if passion >= overwhelming_thresh:
            return True, net_willingness, f"Overwhelming passion ({passion:.1f}) overcame public hesitation"

        # Explicit exhibitionist / hedonist inclination
        if exhibitionism >= float(priv_cfg.get("voyeurism_threshold", 20.0)) or tag_bonus >= 25.0:
            return True, net_willingness, f"Exhibitionist inclination ({net_willingness:.1f}) embraced public encounter"

        # Elastic comparison
        if net_willingness >= exposure_pressure:
            return True, net_willingness, f"Romantic attraction and uninhibited mindset embraced public tryst ({net_willingness:.1f} >= {exposure_pressure:.1f})"

        return False, net_willingness, f"Declined public exposure: preferred a private bedchamber (willingness: {net_willingness:.1f} < {exposure_pressure:.1f})"

    def evaluate_consent_and_privacy(
        self,
        actor: Any,
        partner: Any,
        action_name: str = "private_intimacy",
        context: Optional[Any] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Evaluates Bilateral Dyadic Consent, Elastic Spatial Privacy, and Chemistry:
        1. Co-location Check: Both agents must be physically present in the exact same room.
        2. Somatic Partner State: Partner must have energy >= min_energy and stress <= max_stress.
        3. Continuous Chemistry & Consent: Chemistry must meet threshold.
        4. Elastic Privacy & Exhibitionism: Modesty vs Exhibitionism/Thrill/Alcohol trade-off.
        """
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        act_cfg = rom_cfg.get("actions", {}).get(action_name, {})
        priv_cfg = rom_cfg.get("elastic_privacy_and_exhibitionism", rom_cfg.get("privacy_and_space", {}))
        chem_cfg = rom_cfg.get("relationship_chemistry", {})

        # 1. Co-location Check
        if actor.location_id != partner.location_id:
            return False, f"Partner {partner.name} is not co-located in {actor.location_id}.", {}

        # 2. Somatic State of Partner (No Non-Consensual / Exhaustion Overrides)
        p_energy = float(partner.needs.get("energy", 100.0))
        p_stress = float(partner.get_feeling("stress"))
        min_e = float(act_cfg.get("min_partner_energy", 20.0))
        max_s = float(act_cfg.get("max_partner_stress", 75.0))

        if p_energy < min_e:
            self.total_intimacy_rejections += 1
            return False, f"Partner {partner.name} is too exhausted (energy {p_energy:.1f}) and declined.", {"reason": "EXHAUSTION"}
        if p_stress > max_s:
            self.total_intimacy_rejections += 1
            return False, f"Partner {partner.name} is under acute stress (stress {p_stress:.1f}) and declined.", {"reason": "STRESS"}

        # 3. Continuous Chemistry Evaluation
        bond = self.get_or_create_bond(actor.id, partner.id)
        chemistry = bond.calculate_continuous_chemistry(actor_energy=p_energy, actor_stress=p_stress)
        threshold = float(chem_cfg.get("chemistry_consent_threshold", 30.0))

        if chemistry < threshold:
            self.total_intimacy_rejections += 1
            return False, f"Partner {partner.name} felt insufficient romantic chemistry (chemistry {chemistry:.1f} < {threshold:.1f}).", {"reason": "CHEMISTRY_DEFICIT"}

        # 4. Spatial Privacy & Elastic Exhibitionist Check
        room_id = (actor.location_id or "").lower()
        priv_keywords = priv_cfg.get("private_room_keywords", ["bedroom", "quarters", "loft", "cellar", "chambers", "cottage", "secluded"])
        is_private_room = any(k in room_id for k in priv_keywords)

        # Check third-party witnesses
        witnesses = []
        if context and hasattr(context, "npcs"):
            witnesses = [
                n for n in context.npcs.values()
                if n.id not in (actor.id, partner.id) and n.location_id == actor.location_id and getattr(n, "is_alive", True)
            ]

        is_clandestine_public = not is_private_room or len(witnesses) > 0

        # Elastic Public Exposure Willingness
        actor_willing, actor_score, actor_reason = self.calculate_public_intimacy_willingness(actor, len(witnesses), is_private_room, bond)
        partner_willing, partner_score, partner_reason = self.calculate_public_intimacy_willingness(partner, len(witnesses), is_private_room, bond)

        if is_clandestine_public:
            if not actor_willing:
                return False, f"{actor.name} hesitated: {actor_reason}", {"reason": "PUBLIC_INHIBITION", "target": actor.name, "details": actor_reason}
            if not partner_willing:
                self.total_intimacy_rejections += 1
                return False, f"{partner.name} hesitated: {partner_reason}", {"reason": "PUBLIC_INHIBITION", "target": partner.name, "details": partner_reason}

        # Check if this qualifies as an exhibitionist thrill act
        is_exhibitionist_act = is_clandestine_public and (
            actor_score >= 35.0 or partner_score >= 35.0
            or "TAG_EXHIBITIONIST" in getattr(actor, "tags", set())
            or "TAG_EXHIBITIONIST" in getattr(partner, "tags", set())
            or float(getattr(actor, "vices", {}).get("exhibitionism", 0.0)) >= 20.0
            or float(getattr(partner, "vices", {}).get("exhibitionism", 0.0)) >= 20.0
        )

        details = {
            "chemistry": chemistry,
            "is_private_room": is_private_room,
            "witnesses_count": len(witnesses),
            "is_clandestine_public": is_clandestine_public,
            "is_exhibitionist_act": is_exhibitionist_act,
            "actor_willingness": actor_score,
            "partner_willingness": partner_score,
            "witness_ids": [w.id for w in witnesses]
        }
        return True, "Consensual intimate agreement reached.", details

    def check_and_emit_relational_scandals(
        self,
        actor: Any,
        partner: Any,
        details: Dict[str, Any],
        context: Any,
        current_tick: int
    ) -> Optional[Dict[str, Any]]:
        """
        Emits ambient acoustic & visual information waves when an intimacy act is witnessed
        or constitutes an exclusivity breach (infidelity).
        Incorporates Voyeur vs Prudish witness dynamics.
        """
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        priv_cfg = rom_cfg.get("elastic_privacy_and_exhibitionism", rom_cfg.get("privacy_and_space", {}))
        voy_cfg = priv_cfg.get("voyeur_dynamics", {})
        prud_cfg = priv_cfg.get("prudish_dynamics", {})

        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
        if not info_eng:
            return None

        # Check Infidelity (Breach of Monogamous Marriage/Betrothal)
        actor_spouse_id = actor.social_profile.get("spouse_id")
        partner_spouse_id = partner.social_profile.get("spouse_id")

        is_infidelity = False
        betrayed_spouse = None
        if actor_spouse_id and actor_spouse_id != partner.id:
            is_infidelity = True
            betrayed_spouse = context.npcs.get(actor_spouse_id)
        elif partner_spouse_id and partner_spouse_id != actor.id:
            is_infidelity = True
            betrayed_spouse = context.npcs.get(partner_spouse_id)

        # 1. Process Witnesses: Voyeurs vs Moralistic/Prudish
        voyeur_threshold = float(voy_cfg.get("voyeurism_threshold", 20.0))
        titill_gain = float(voy_cfg.get("titillation_gain", 25.0))
        cont_gain = float(voy_cfg.get("contentment_gain", 15.0))
        indig_gain = float(prud_cfg.get("indignation_gain", 25.0))
        stress_gain = float(prud_cfg.get("stress_gain", 15.0))

        witnesses = [
            context.npcs[w_id] for w_id in details.get("witness_ids", [])
            if w_id in context.npcs and getattr(context.npcs[w_id], "is_alive", True)
        ]
        voyeur_witnesses = []
        moral_witnesses = []

        for w in witnesses:
            w_vices = getattr(w, "vices", {}) or {}
            w_p = getattr(w, "personality", {}) or {}
            w_sp = getattr(w, "social_profile", {}) or {}
            w_tags = getattr(w, "tags", set()) or set()

            w_voyeurism = float(w_vices.get("voyeurism", 0.0))
            w_openness = float(w_p.get("openness", 0.5))
            w_honor = float(w_sp.get("moral_values", {}).get("honor", 0.5))

            is_voyeur = (
                w_voyeurism >= voyeur_threshold
                or "TAG_VOYEUR" in w_tags
                or "voyeur" in str(w_tags).lower()
                or (w_openness >= 0.70 and w_honor <= 0.50)
            )

            time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

            if is_voyeur:
                # Voyeur gains titillation, amusement, and contentment!
                w.adjust_feeling("titillation", titill_gain)
                w.adjust_feeling("contentment", cont_gain)
                w.adjust_feeling("stress", -8.0)
                voyeur_witnesses.append(w)
                w.record_biographical_entry(
                    current_tick, time_iso, "VOYEUR_SPECTACLE",
                    f"Observed an uninhibited intimate encounter at {actor.location_id} with intense voyeuristic fascination."
                )
            else:
                # Moralistic onlooker gains indignation and stress
                w.adjust_feeling("indignation", indig_gain)
                w.adjust_feeling("stress", stress_gain)
                moral_witnesses.append(w)

        # 2. Public Tryst Scandal Wave Emission
        if details.get("is_clandestine_public") and details.get("witnesses_count", 0) > 0:
            self.total_scandals_emitted += 1
            base_intensity = float(priv_cfg.get("public_tryst_scandal_intensity", 0.90))

            # If ALL witnesses are voyeurs, scandal emission is suppressed into a titillating whisper!
            if voyeur_witnesses and not moral_witnesses:
                base_intensity *= float(voy_cfg.get("scandal_suppression_factor", 0.50))
                topic = "VOYEUR_CLANDESTINE_SECRET"
                headline = f"Whispered Secret: Clandestine Intimacy Witnessed at {actor.location_id}"
                content = f"Discreet onlookers observed a thrilling encounter between {actor.name} and {partner.name}."
            else:
                if any(getattr(w, "social_profile", {}).get("moral_values", {}).get("honor", 0.5) > 0.7 for w in moral_witnesses):
                    base_intensity *= float(prud_cfg.get("scandal_intensity_multiplier", 1.25))
                topic = "SCANDALOUS_PUBLIC_TRYST"
                headline = f"Tavern Gossip: Indecent Tryst Observed at {actor.location_id}"
                content = f"Citizens witnessed an indiscreet romantic encounter between {actor.name} and {partner.name}."

            info_item = info_eng.publish_item(
                channel=InformationChannelType.GOSSIP_AND_RUMORS,
                topic=topic,
                headline=headline,
                content=content,
                source_npc_id=actor.id,
                target_location_id=actor.location_id,
                current_tick=current_tick,
                context=context
            )
            from src.society.information_networks import WaveMedium
            info_eng.emit_ambient_wave(
                item=info_item,
                origin_room_id=actor.location_id,
                medium=WaveMedium.ACOUSTIC_SOUND,
                intensity=round(min(1.0, base_intensity), 2),
                context=context,
                current_tick=current_tick
            )

        # 3. Infidelity Scandal & Grudge Influx
        if is_infidelity and betrayed_spouse:
            self.jealousy_triggers_count += 1
            grudge_potency = float(priv_cfg.get("infidelity_grudge_potency", 65.0))
            betrayed_spouse.adjust_feeling("resentment", 45.0)
            betrayed_spouse.adjust_feeling("jealousy", 50.0)
            betrayed_spouse.adjust_feeling("grief", 35.0)

            if betrayed_spouse.location_id == actor.location_id or details.get("witnesses_count", 0) > 0:
                self.total_scandals_emitted += 1
                info_item = info_eng.publish_item(
                    channel=InformationChannelType.GOSSIP_AND_RUMORS,
                    topic="BETRAYAL_INFIDELITY",
                    headline=f"Scandal: Marital Infidelity Discovered Between {actor.name} and {partner.name}",
                    content=f"{betrayed_spouse.name}'s marital bond was compromised by a clandestine liaison.",
                    source_npc_id=betrayed_spouse.id if betrayed_spouse.location_id == actor.location_id else actor.id,
                    target_location_id=actor.location_id,
                    current_tick=current_tick,
                    context=context
                )
                from src.society.information_networks import WaveMedium
                info_eng.emit_ambient_wave(
                    item=info_item,
                    origin_room_id=actor.location_id,
                    medium=WaveMedium.VISUAL_LINE_OF_SIGHT,
                    intensity=float(priv_cfg.get("infidelity_scandal_intensity", 1.0)),
                    context=context,
                    current_tick=current_tick
                )
                return {
                    "infidelity_detected": True,
                    "betrayed_spouse": betrayed_spouse.name,
                    "voyeur_witnesses": len(voyeur_witnesses),
                    "moral_witnesses": len(moral_witnesses)
                }

        return {
            "infidelity_detected": False,
            "voyeur_witnesses": len(voyeur_witnesses),
            "moral_witnesses": len(moral_witnesses)
        }

        # Check Infidelity (Breach of Monogamous Marriage/Betrothal)
        actor_spouse_id = actor.social_profile.get("spouse_id")
        partner_spouse_id = partner.social_profile.get("spouse_id")

        is_infidelity = False
        betrayed_spouse = None
        if actor_spouse_id and actor_spouse_id != partner.id:
            is_infidelity = True
            betrayed_spouse = context.npcs.get(actor_spouse_id)
        elif partner_spouse_id and partner_spouse_id != actor.id:
            is_infidelity = True
            betrayed_spouse = context.npcs.get(partner_spouse_id)

        # 1. Public Tryst Scandal (witnessed in public/semi-public space)
        if details.get("is_clandestine_public") and details.get("witnesses_count", 0) > 0:
            self.total_scandals_emitted += 1
            info_item = info_eng.publish_item(
                channel=InformationChannelType.GOSSIP_AND_RUMORS,
                topic="SCANDALOUS_PUBLIC_TRYST",
                headline=f"Tavern Gossip: Indecent Tryst Observed at {actor.location_id}",
                content=f"Citizens witnessed an indiscreet romantic encounter between {actor.name} and {partner.name}.",
                source_npc_id=actor.id,
                target_location_id=actor.location_id,
                current_tick=current_tick,
                context=context
            )
            from src.society.information_networks import WaveMedium
            info_eng.emit_ambient_wave(
                item=info_item,
                origin_room_id=actor.location_id,
                medium=WaveMedium.ACOUSTIC_SOUND,
                intensity=float(priv_cfg.get("public_tryst_scandal_intensity", 0.90)),
                context=context,
                current_tick=current_tick
            )

        # 2. Infidelity Scandal & Grudge Influx
        if is_infidelity and betrayed_spouse:
            self.jealousy_triggers_count += 1
            # Infidelity grudge
            grudge_potency = float(priv_cfg.get("infidelity_grudge_potency", 65.0))
            betrayed_spouse.adjust_feeling("resentment", 45.0)
            betrayed_spouse.adjust_feeling("jealousy", 50.0)
            betrayed_spouse.adjust_feeling("grief", 35.0)

            # If betrayed spouse is co-located or witnessed it, emit high-credibility rumor
            if betrayed_spouse.location_id == actor.location_id or details.get("witnesses_count", 0) > 0:
                self.total_scandals_emitted += 1
                info_item = info_eng.publish_item(
                    channel=InformationChannelType.GOSSIP_AND_RUMORS,
                    topic="BETRAYAL_INFIDELITY",
                    headline=f"Scandal: Marital Infidelity Discovered Between {actor.name} and {partner.name}",
                    content=f"{betrayed_spouse.name}'s marital bond was compromised by a clandestine liaison.",
                    source_npc_id=betrayed_spouse.id if betrayed_spouse.location_id == actor.location_id else actor.id,
                    target_location_id=actor.location_id,
                    current_tick=current_tick,
                    context=context
                )
                from src.society.information_networks import WaveMedium
                info_eng.emit_ambient_wave(
                    item=info_item,
                    origin_room_id=actor.location_id,
                    medium=WaveMedium.VISUAL_LINE_OF_SIGHT,
                    intensity=float(priv_cfg.get("infidelity_scandal_intensity", 1.0)),
                    context=context,
                    current_tick=current_tick
                )
                return {"infidelity_detected": True, "betrayed_spouse": betrayed_spouse.name}

        return None


    def execute_autonomous_intimacy(self, actor: Any, partner: Any, context: Any, tick: int) -> Dict[str, Any]:
        from src.behaviours.actions import ActionRegistry
        return ActionRegistry.execute_private_intimacy(actor, partner, current_tick=tick, context=context)
