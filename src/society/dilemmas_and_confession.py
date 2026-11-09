"""
Moral Dilemmas, Transgression Guilt, and Therapeutic Social Outlets.
Operates 100% on declarative configurations from data/settings/dilemmas.json.
Models psychological guilt accumulation, spiritual confession in the chapel with clergy,
confiding secrets with companion leak risk, and continuous multi-faceted reputation.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

class MoralDilemmaEngine:
    """
    Central Moral Dilemma and Therapeutic Confession Engine.
    Tracks ethical transgressions, updates continuous guilt and reputation facets,
    resolves spiritual absolution in the chapel, and handles confiding in trusted peers.
    """
    _instance: Optional["MoralDilemmaEngine"] = None

    @classmethod
    def get_instance(cls) -> "MoralDilemmaEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.transgression_history: List[Dict[str, Any]] = []
        self.confession_history: List[Dict[str, Any]] = []
        self.total_guilt_absolved_count: int = 0
        self.total_secrets_confided_count: int = 0
        self.total_secrets_leaked_count: int = 0

    def get_dilemmas_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("dilemmas")

    def record_transgression(
        self,
        transgressor: Any,
        transgression_type: str,
        context: Any,
        tick: int = 0,
        victim_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records an ethical or legal transgression:
        1. Injects psychological guilt and somatic stress into transgressor.
        2. Erodes moral integrity.
        3. Penalizes trustworthiness in the multi-faceted social profile.
        """
        cfg = self.get_dilemmas_config()
        t_defs = cfg.get("transgressions", {})
        spec = t_defs.get(transgression_type, {})

        guilt_gain = float(spec.get("base_guilt", 25.0))
        stress_gain = float(spec.get("base_stress", 20.0))
        erosion_delta = float(spec.get("moral_erosion_delta", 3.0))
        trust_penalty = float(spec.get("trustworthiness_penalty", 25.0))

        transgressor.adjust_feeling("guilt", guilt_gain)
        transgressor.adjust_feeling("stress", stress_gain)
        if hasattr(transgressor, "adjust_moral_erosion"):
            transgressor.adjust_moral_erosion(erosion_delta)

        # Update multi-faceted reputation facets in social_profile
        sp = getattr(transgressor, "social_profile", {}) or {}
        facets = sp.setdefault("reputation_facets", {
            "trustworthiness": 75.0,
            "civic_standing": 50.0,
            "moral_piety": 50.0
        })
        facets["trustworthiness"] = max(0.0, round(facets.get("trustworthiness", 75.0) - trust_penalty, 2))
        facets["moral_piety"] = max(0.0, round(facets.get("moral_piety", 50.0) - (trust_penalty * 0.5), 2))

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        record = {
            "transgressor_id": transgressor.id,
            "transgressor_name": transgressor.name,
            "transgression_type": transgression_type,
            "victim_id": victim_id,
            "guilt_gain": guilt_gain,
            "new_trustworthiness": facets["trustworthiness"],
            "tick": tick
        }
        self.transgression_history.append(record)
        transgressor.record_biographical_entry(
            tick, time_iso, "MORAL_TRANSGRESSION",
            f"Committed {spec.get('name', transgression_type)}, suffering guilt and compromising reputation."
        )
        return record

    def seek_spiritual_confession(
        self,
        penitent: Any,
        priest: Any,
        context: Any,
        tick: int = 0
    ) -> Dict[str, Any]:
        """
        Spiritual Confession in Sacred Space (Chapel/Sanctuary):
        Penitent donates modest alms, unburdens sins to clergy, and receives absolution.
        Relieves guilt and stress, restores moral erosion, and enhances piety standing.
        """
        cfg = self.get_dilemmas_config()
        ther_cfg = cfg.get("therapeutic_mechanisms", {}).get("spiritual_confession", {})
        alms_due = float(ther_cfg.get("alms_donation_gold", 0.50))

        # Check co-location in sacred room
        room_id = (penitent.location_id or "").lower()
        sacred_kws = ther_cfg.get("sacred_room_keywords", ["chapel", "sanctuary", "church"])
        if not any(k in room_id for k in sacred_kws):
            return {"success": False, "reason": "Confession must take place within a chapel or sacred sanctuary."}

        if penitent.location_id != priest.location_id:
            return {"success": False, "reason": f"Clergy {priest.name} is not present in {penitent.location_id}."}

        # Check alms affordability
        actual_alms = min(float(getattr(penitent, "wealth", 0.0)), alms_due)
        if actual_alms > 0:
            penitent.wealth = round(penitent.wealth - actual_alms, 2)
            priest.wealth = round(priest.wealth + actual_alms, 2)
            treasury = getattr(context, "municipal_treasury", None)
            if treasury and hasattr(treasury, "balance"):
                # Tithe portion to community
                treasury.balance = round(treasury.balance + (actual_alms * 0.20), 2)

        guilt_relief = float(ther_cfg.get("guilt_reduction", -35.0))
        stress_relief = float(ther_cfg.get("stress_relief", -25.0))
        erosion_relief = float(ther_cfg.get("moral_erosion_relief", -10.0))
        piety_boost = float(ther_cfg.get("piety_standing_gain", 15.0))

        penitent.adjust_feeling("guilt", guilt_relief)
        penitent.adjust_feeling("stress", stress_relief)
        penitent.adjust_feeling("contentment", 15.0)
        if hasattr(penitent, "adjust_moral_erosion"):
            penitent.adjust_moral_erosion(erosion_relief)

        # Enhance piety standing
        sp = getattr(penitent, "social_profile", {}) or {}
        facets = sp.setdefault("reputation_facets", {"trustworthiness": 75.0, "civic_standing": 50.0, "moral_piety": 50.0})
        facets["moral_piety"] = min(100.0, round(facets.get("moral_piety", 50.0) + piety_boost, 2))

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        penitent.record_biographical_entry(
            tick, time_iso, "SPIRITUAL_CONFESSION",
            f"Confessed worldly transgressions to Father {priest.name} in {penitent.location_id}, receiving holy absolution."
        )
        priest.record_biographical_entry(
            tick, time_iso, "PASTORAL_ABSOLUTION",
            f"Heard confession and administered spiritual absolution to {penitent.name}."
        )

        self.total_guilt_absolved_count += 1
        case = {
            "success": True,
            "penitent_id": penitent.id,
            "priest_id": priest.id,
            "alms_donated_gold": actual_alms,
            "guilt_relieved": abs(guilt_relief),
            "new_piety": facets["moral_piety"]
        }
        self.confession_history.append(case)
        return case

    def confide_in_companion(
        self,
        confider: Any,
        confidant: Any,
        secret_topic: str,
        context: Any,
        tick: int = 0
    ) -> Dict[str, Any]:
        """
        Confides an agonizing secret or guilt to a trusted companion.
        Deepens reciprocal trust and relieves guilt, but risks gossip leakage if confidant is gossipy.
        """
        cfg = self.get_dilemmas_config()
        ther_cfg = cfg.get("therapeutic_mechanisms", {}).get("confide_in_friend", {})
        min_trust = float(ther_cfg.get("min_trust_threshold", 60.0))

        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        trust_val = op_eng.get_net_opinion(confider.id, confidant.id) if op_eng and hasattr(op_eng, "get_net_opinion") else 50.0

        if trust_val < min_trust:
            return {"success": False, "reason": f"Insufficient trust to confide ({trust_val:.1f} < {min_trust:.1f})."}

        guilt_relief = float(ther_cfg.get("guilt_reduction", -20.0))
        stress_relief = float(ther_cfg.get("stress_relief", -18.0))
        trust_gain = float(ther_cfg.get("mutual_trust_gain", 8.0))

        confider.adjust_feeling("guilt", guilt_relief)
        confider.adjust_feeling("stress", stress_relief)
        confider.adjust_feeling("tenderness", 10.0)
        confidant.adjust_feeling("pride", 8.0) # Trusted with secret

        if op_eng:
            op_eng.add_modifier(from_npc=confider, to_npc=confidant, mod_id="confided_secret", desc="Shared deep secret", delta=trust_gain, tick=tick)
            op_eng.add_modifier(from_npc=confidant, to_npc=confider, mod_id="entrusted_secret", desc="Entrusted with companion's secret", delta=trust_gain, tick=tick)

        self.total_secrets_confided_count += 1

        # Evaluate Leak Risk based on confidant extraversion and discretion
        conf_p = getattr(confidant, "personality", {}) or {}
        conf_ext = float(conf_p.get("extraversion", 0.5))
        conf_cons = float(conf_p.get("conscientiousness", 0.5))

        leak_risk = max(0.05, min(0.75, (conf_ext * 0.45) - (conf_cons * 0.25)))
        roll = context.random.random() if hasattr(context, "random") and hasattr(context.random, "random") else 0.5
        leaked = (roll < leak_risk)

        if leaked:
            self.total_secrets_leaked_count += 1
            info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
            if info_eng:
                from src.society.information_networks import InformationChannelType
                info_eng.publish_item(
                    channel=InformationChannelType.GOSSIP_AND_RUMORS,
                    topic=f"LEAKED_SECRET_{secret_topic.upper()}",
                    headline=f"Tavern Whispers: Secret Concerning {confider.name} Revealed",
                    content=f"Word leaked from a private conversation that {confider.name} harbored secrets regarding {secret_topic}.",
                    source_npc_id=confidant.id,
                    target_location_id=confidant.location_id,
                    current_tick=tick,
                    context=context
                )

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        confider.record_biographical_entry(
            tick, time_iso, "CONFIDED_SECRET",
            f"Unburdened an agonizing secret regarding {secret_topic} to companion {confidant.name}."
        )

        return {
            "success": True,
            "confider": confider.name,
            "confidant": confidant.name,
            "guilt_relieved": abs(guilt_relief),
            "leaked_to_gossip": leaked
        }
