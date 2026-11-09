"""Autonomous NPC Entity with S-Curve Metabolic Hunger Decay & Career Ledgers."""
from typing import Any, Dict, List, Optional, Tuple
from src.entities.base import BaseEntity
from src.entities.item import ItemInstance
from src.entities.status_tags import TaggedEntityMixin, StatusTag, TagScope
from src.entities.fulfillment import FulfillmentProfile, FulfillmentType

class NPC(BaseEntity, TaggedEntityMixin):
    _feelings_config: Optional[Dict[str, Any]] = None
    _envelope_engine: Optional[Any] = None
    _romance_config: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        npc_id: str,
        name: str,
        location_id: Optional[str] = None,
        occupation: str = "Commoner",
        home_location_id: Optional[str] = None,
        work_location_id: Optional[str] = None,
        needs: Optional[Dict[str, float]] = None,
        decay_rates: Optional[Dict[str, float]] = None,
        attributes: Optional[Dict[str, float]] = None,
        personality: Optional[Dict[str, float]] = None,
        inventory: Optional[List[ItemInstance]] = None,
        wealth: float = 50.0,
        faction_id: Optional[str] = None,
        civic_role: Optional[str] = None,
        social_profile: Optional[Dict[str, Any]] = None,
        feelings: Optional[Dict[str, float]] = None,
        moral_erosion: float = 10.0,
        skills: Optional[Dict[str, float]] = None,
        physical_attributes: Optional[Dict[str, float]] = None,
        mental_attributes: Optional[Dict[str, float]] = None,
        career_statistics: Optional[Dict[str, Any]] = None,
        fulfillment: Optional[Any] = None,
        vices: Optional[Dict[str, float]] = None,
        cognition: Optional[Dict[str, Any]] = None,
        mental_map: Optional[Dict[str, Any]] = None,
        acquaintances: Optional[Dict[str, Any]] = None,
        biographical_log: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(npc_id, name, "npc", location_id)
        TaggedEntityMixin.__init__(self)
        self.occupation = occupation
        self.home_location_id = home_location_id
        self.work_location_id = work_location_id

        self.needs: Dict[str, float] = {"hunger": 20.0, "energy": 90.0, "social": 50.0}
        if needs:
            self.needs.update(needs)

        self.decay_rates: Dict[str, float] = {"hunger": 0.05, "energy": -0.07, "social": -0.05}
        if decay_rates:
            self.decay_rates.update(decay_rates)

        self.attributes = attributes or {"strength": 10.0, "intelligence": 10.0, "stamina": 10.0}
        self.personality = personality or {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
        self.inventory: List[ItemInstance] = inventory if inventory is not None else []
        self._wealth = max(0.0, round(float(wealth), 2))
        self.current_state = "IDLE"
        self.current_action = "IDLE"
        self.faction_id = faction_id
        self.civic_role = civic_role

        self.social_profile = social_profile or {
            "moral_values": {"loyalty": 0.7, "honor": 0.8, "ambition": 0.5},
            "reputation_facets": {"trustworthiness": 75.0, "temperament": 50.0},
            "social_class": "COMMONER",
            "background": "Local citizen with deep roots."
        }

        self.feelings: Dict[str, float] = {
            "contentment": 50.0, "tenderness": 20.0, "passion": 15.0,
            "loneliness": 10.0, "stress": 10.0, "jealousy": 0.0,
            "guilt": 0.0, "grief": 0.0, "pride": 30.0, "resentment": 0.0
        }
        if feelings:
            self.feelings.update(feelings)

        self.moral_erosion: float = max(0.0, min(100.0, moral_erosion))
        self.action_resistance: Dict[str, float] = {}
        self.biographical_log: List[Dict[str, Any]] = list(biographical_log or [])

        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()
        self.skills: Dict[str, float] = dict(skills or occ_reg.get_default_skills(occupation))

        self.physical_attributes: Dict[str, float] = physical_attributes or {
            "constitution": 50.0, "work_rate": 55.0, "agility": 50.0, "pain_tolerance": 45.0, "recovery_rate": 50.0
        }
        self.mental_attributes: Dict[str, float] = mental_attributes or {
            "composure": 50.0, "ambition": 50.0, "leadership": 40.0, "adaptability": 50.0, "loyalty": 60.0, "shrewdness": 45.0
        }

        self.career_statistics: Dict[str, Any] = career_statistics or {
            "career_earnings_gold": 0.0,
            "taxes_paid_gold": 0.0,
            "goods_crafted_count": 0,
            "trades_executed_count": 0,
            "contracts_fulfilled": 0,
            "crimes_committed": 0,
        }

        self.fulfillment = fulfillment if isinstance(fulfillment, FulfillmentProfile) else FulfillmentProfile()
        self.vices = vices or {"alcohol_dependence": 0.0, "gambling_drive": 0.0, "crime_propensity": 0.0, "vice_indulgence": 0.0}
        self.cognition = cognition or {"decision_quality": "Rational", "laziness": 0.2}
        self.mental_map = mental_map or {}
        self.acquaintances = acquaintances or {}

        self.intimacy_drive: float = 50.0
        self.unmet_intimacy_tension: float = 10.0
        self.last_intimacy_tick: int = 0
        self.household_id: Optional[str] = None
        self._unassessed_earnings_gold: float = 0.0
        self._satiety_buffer_until_tick: int = 0
        self.intent_horizon: Optional[Any] = None
        self.active_thoughts: List[Dict[str, Any]] = []
        self.dominant_thought: Optional[Dict[str, Any]] = None
        self.thought_history: List[Dict[str, Any]] = []

    @property
    def is_alive(self) -> bool:
        return self.current_state != "DECEASED"

    @property
    def wealth(self) -> float:
        return self._wealth

    @wealth.setter
    def wealth(self, val: float) -> None:
        delta = round(float(val), 2) - self._wealth
        if delta > 0.0:
            self._unassessed_earnings_gold = round(self._unassessed_earnings_gold + delta, 2)
        self._wealth = max(0.0, round(float(val), 2))

    def calculate_hunger_decay(self, current_action: Optional[str] = None, current_tick: int = 0) -> float:
        """Dynamic S-Curve Metabolic Hunger Decay Scaling on Physical & Mental Exertion (Declarative)."""
        from src.configuration.settings import SettingsRegistry
        phys_cfg = SettingsRegistry.get_instance().get("physiology")
        meta_cfg = phys_cfg.get("metabolic_decay", {})

        satiety_decay = float(meta_cfg.get("satiety_buffer_decay", 0.008))
        if hasattr(self, "_satiety_buffer_until_tick") and current_tick < self._satiety_buffer_until_tick:
            return satiety_decay

        act = (current_action or getattr(self, "current_action", "IDLE") or "").upper()
        action_mults = meta_cfg.get("action_exertion_multipliers", {})
        p_exertion = float(action_mults.get(act, action_mults.get("DEFAULT", 0.85)))

        stress = float(self.get_feeling("stress"))
        m_exertion = 0.5 + (stress / 100.0) * 0.7

        work_rate = float(self.physical_attributes.get("work_rate", 55.0)) / 55.0
        constitution = float(self.physical_attributes.get("constitution", 50.0))
        const_factor = max(0.80, 1.25 - (constitution / 100.0) * 0.45)

        p_weight = float(meta_cfg.get("physical_exertion_weight", 0.70))
        m_weight = float(meta_cfg.get("mental_exertion_weight", 0.30))
        composite_exertion = (p_weight * p_exertion * work_rate * const_factor) + (m_weight * m_exertion)
        base_rate = float(meta_cfg.get("base_rate", 0.055))
        exp = float(meta_cfg.get("composite_exertion_exponent", 1.15))
        min_clamp = float(meta_cfg.get("min_rate_clamp", 0.018))
        max_clamp = float(meta_cfg.get("max_rate_clamp", 0.180))

        scaled_rate = base_rate * (composite_exertion ** exp)

        # Continuous Somatic Thermal Thermogenesis Scaling (Declarative)
        temp_val = getattr(self, "_current_room_temperature", None)
        if temp_val is not None and temp_val < 18.0:
            clim_cfg = SettingsRegistry.get_instance().get("weather_and_climate").get("climate_system", {})
            somatic_cfg = clim_cfg.get("somatic_comfort", {})
            exp_cold = float(somatic_cfg.get("cold_metabolic_scaling_exponent", 1.8))
            max_cold_boost = float(somatic_cfg.get("cold_max_metabolic_boost", 0.65))
            deficit = max(0.0, 18.0 - temp_val) / 18.0
            cold_mult = 1.0 + min(max_cold_boost, (deficit ** exp_cold) * max_cold_boost)
            scaled_rate *= cold_mult

        return round(max(min_clamp, min(max_clamp, scaled_rate)), 4)

    def apply_continuous_decay(self, delta_ticks: int = 1, current_tick: int = 0) -> None:
        """Continuous analytical decay of physiological needs and emotional feelings over delta_ticks."""
        if delta_ticks <= 0:
            return
        from src.configuration.settings import SettingsRegistry
        phys_cfg = SettingsRegistry.get_instance().get("physiology")
        defaults = phys_cfg.get("need_decay_defaults", {})

        h_rate = self.calculate_hunger_decay(self.current_action, current_tick)
        self.needs["hunger"] = min(100.0, max(0.0, self.needs.get("hunger", 0.0) + (h_rate * delta_ticks)))
        e_rate = self.decay_rates.get("energy", defaults.get("energy", -0.07))
        self.needs["energy"] = min(100.0, max(0.0, self.needs.get("energy", 0.0) + (e_rate * delta_ticks)))
        s_rate = self.decay_rates.get("social", defaults.get("social", -0.05))
        self.needs["social"] = min(100.0, max(0.0, self.needs.get("social", 0.0) + (s_rate * delta_ticks)))

        # Continuous feelings relaxation towards equilibrium
        feelings_cfg = phys_cfg.get("feelings_homeostasis", {})
        neg_decay = float(feelings_cfg.get("negative_feelings_decay", 0.003))
        target_c = float(feelings_cfg.get("contentment_equilibrium", 50.0))
        drift_up = float(feelings_cfg.get("contentment_drift_up", 0.002))
        drift_down = float(feelings_cfg.get("contentment_drift_down", 0.003))

        for f_name in ("grief", "jealousy", "guilt", "resentment", "stress"):
            val = self.feelings.get(f_name, 0.0)
            if val > 0.0:
                self.feelings[f_name] = max(0.0, round(val - (neg_decay * delta_ticks), 3))

        curr_c = self.feelings.get("contentment", target_c)
        if curr_c > target_c:
            self.feelings["contentment"] = max(target_c, round(curr_c - (drift_down * delta_ticks), 3))
        elif curr_c < target_c:
            self.feelings["contentment"] = min(target_c, round(curr_c + (drift_up * delta_ticks), 3))

        # Continuous coupling: Depleted social need generates loneliness; satisfied social relaxes it
        social_need = self.needs.get("social", 50.0)
        if social_need < 25.0:
            soc_deficit = (25.0 - social_need) / 25.0
            self.feelings["loneliness"] = min(100.0, round(self.feelings.get("loneliness", 0.0) + (0.008 * soc_deficit * delta_ticks), 3))
        else:
            self.feelings["loneliness"] = max(0.0, round(self.feelings.get("loneliness", 0.0) - (neg_decay * delta_ticks), 3))

        # Dynamic somatic & socioeconomic friction
        if self.wealth < 5.0:
            self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + (0.008 * delta_ticks), 3))
            self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (0.012 * delta_ticks), 3))
        elif self.wealth < 12.0:
            self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + (0.003 * delta_ticks), 3))

        if self.needs.get("hunger", 0.0) > 40.0:
            h_strain = (self.needs["hunger"] - 40.0) / 60.0
            self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + (0.006 * h_strain * delta_ticks), 3))
            self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (0.010 * h_strain * delta_ticks), 3))

        if self.needs.get("energy", 100.0) < 25.0:
            e_strain = (25.0 - self.needs["energy"]) / 25.0
            self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + (0.008 * e_strain * delta_ticks), 3))
            self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (0.010 * e_strain * delta_ticks), 3))

        if self.feelings.get("loneliness", 0.0) > 30.0:
            l_strain = (self.feelings["loneliness"] - 30.0) / 70.0
            self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (0.008 * l_strain * delta_ticks), 3))

        # Somatic thermal stress & hypothermia
        temp_val = getattr(self, "_current_room_temperature", None)
        if temp_val is not None:
            clim_cfg = SettingsRegistry.get_instance().get("weather_and_climate").get("climate_system", {})
            somatic_cfg = clim_cfg.get("somatic_comfort", {})
            shiver_t = float(somatic_cfg.get("shivering_threshold_celsius", 12.0))
            freeze_rate = float(somatic_cfg.get("freezing_stress_penalty_rate", 0.025))
            if temp_val < shiver_t:
                deficit = (shiver_t - temp_val) / max(1.0, shiver_t)
                stress_gain = freeze_rate * (1.0 + deficit) * delta_ticks
                self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + stress_gain, 3))
                self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (stress_gain * 1.5), 3))

        # Outdoor shelter exposure penalty on sleep & rest
        r_loc = (self.location_id or "").lower()
        is_outdoor = any(k in r_loc for k in ("square", "plaza", "quay", "street", "road", "field", "garden", "market"))
        if is_outdoor and getattr(self, "current_action", "") in ("SLEEP_REST", "COLLAPSE_FATIGUE"):
            self.feelings["stress"] = min(100.0, round(self.feelings.get("stress", 0.0) + (0.012 * delta_ticks), 3))
            self.feelings["contentment"] = max(5.0, round(self.feelings.get("contentment", 50.0) - (0.015 * delta_ticks), 3))

        # Criminal probation tag expiration
        if current_tick >= getattr(self, "criminal_probation_until_tick", 0) and hasattr(self, "has_tag") and self.has_tag("TAG_CONVICTED_CRIMINAL"):
            self.remove_status_tag("TAG_CONVICTED_CRIMINAL")

        self.unmet_intimacy_tension = min(100.0, round(getattr(self, "unmet_intimacy_tension", 10.0) + (0.0015 * delta_ticks), 3))

    def apply_need_decay(self, current_tick: int = 0) -> None:
        self.apply_continuous_decay(delta_ticks=1, current_tick=current_tick)

    def decay_feelings(self) -> None:
        from src.configuration.settings import SettingsRegistry
        phys_cfg = SettingsRegistry.get_instance().get("physiology")
        feelings_cfg = phys_cfg.get("feelings_homeostasis", {})
        neg_decay = float(feelings_cfg.get("negative_feelings_decay", 0.003))
        target_c = float(feelings_cfg.get("contentment_equilibrium", 50.0))
        drift_up = float(feelings_cfg.get("contentment_drift_up", 0.002))
        drift_down = float(feelings_cfg.get("contentment_drift_down", 0.003))

        for f_name in ("grief", "jealousy", "guilt", "resentment", "stress"):
            val = self.feelings.get(f_name, 0.0)
            if val > 0.0:
                self.feelings[f_name] = max(0.0, round(val - neg_decay, 3))
        # Contentment drift towards equilibrium
        curr_c = self.feelings.get("contentment", target_c)
        if curr_c > target_c:
            self.feelings["contentment"] = max(target_c, round(curr_c - drift_down, 3))
        elif curr_c < target_c:
            self.feelings["contentment"] = min(target_c, round(curr_c + drift_up, 3))

    def decay_vices_and_moral_homeostasis(self) -> None:
        from src.configuration.settings import SettingsRegistry
        phys_cfg = SettingsRegistry.get_instance().get("physiology")
        erosion_decay = float(phys_cfg.get("feelings_homeostasis", {}).get("moral_erosion_decay", 0.10))
        if self.moral_erosion > 10.0:
            self.moral_erosion = max(10.0, round(self.moral_erosion - erosion_decay, 2))

    def get_feeling(self, name: str) -> float:
        return self.feelings.get(name, 0.0)

    def set_feeling(self, name: str, val: float) -> None:
        self.feelings[name] = max(0.0, min(100.0, val))

    def adjust_feeling(self, name: str, delta: float, **kwargs: Any) -> float:
        curr = self.get_feeling(name)
        new_val = max(0.0, min(100.0, curr + delta))
        self.feelings[name] = new_val
        return new_val

    def adjust_moral_erosion(self, delta: float) -> float:
        self.moral_erosion = max(0.0, min(100.0, self.moral_erosion + delta))
        return self.moral_erosion

    def get_skill(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 15.0)

    def improve_skill(self, skill_name: str, delta: float = 0.5) -> float:
        new_s = min(100.0, self.get_skill(skill_name) + delta)
        self.skills[skill_name] = round(new_s, 2)
        return new_s

    def record_stat(self, stat_name: str, delta: Any = 1) -> None:
        curr = self.career_statistics.get(stat_name, 0)
        if isinstance(curr, (int, float)) and isinstance(delta, (int, float)):
            self.career_statistics[stat_name] = round(curr + delta, 2)
        else:
            self.career_statistics[stat_name] = delta

    def record_biographical_entry(self, tick: int, time_iso: str, category: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "tick": tick,
            "time_iso": time_iso,
            "category": category,
            "description": description,
            "dominant_mood": self.get_dominant_mood(),
            "wealth": self.wealth,
            "location_id": self.location_id,
            "metadata": metadata or {}
        }
        self.biographical_log.append(entry)
        if len(self.biographical_log) > 50:
            self.biographical_log = self.biographical_log[-50:]
        return entry

    def get_thermal_comfort(self) -> Dict[str, Any]:
        room_t = getattr(self, "_current_room_temperature", 18.0)
        return {
            "room_temperature": round(room_t, 2),
            "is_comfortable": 17.0 <= room_t <= 24.0,
            "is_cold": room_t < 17.0,
            "is_shivering": room_t < 12.0,
            "is_freezing": room_t < 0.0
        }

    def get_thinking_profile(self) -> Dict[str, Any]:
        from src.ai.attentional_mindspace import AttentionalMindspaceEngine
        return AttentionalMindspaceEngine.get_instance().resolve_thinking_profile(self).to_dict()

    def get_dominant_thought(self) -> Optional[Dict[str, Any]]:
        return self.dominant_thought

    def get_dominant_mood(self) -> str:
        if self.get_feeling("grief") > 40.0: return "GRIEVING"
        if self.get_feeling("stress") > 60.0: return "STRESSED"
        if self.get_feeling("resentment") > 40.0: return "BITTER"
        if self.needs.get("energy", 100.0) < 20.0: return "EXHAUSTED"
        if self.get_feeling("passion") > 50.0: return "PASSIONATE"
        if self.get_feeling("tenderness") > 50.0: return "LOVING"
        if self.get_feeling("contentment") >= 50.0: return "CONTENT"
        return "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "occupation": self.occupation,
            "home_location_id": self.home_location_id,
            "work_location_id": self.work_location_id,
            "needs": self.needs,
            "wealth": self.wealth,
            "personality": self.personality,
            "feelings": self.feelings,
            "moral_erosion": self.moral_erosion,
            "skills": self.skills,
            "social_profile": self.social_profile,
            "career_statistics": self.career_statistics,
            "inventory": [i.to_dict() for i in self.inventory],
            "current_state": self.current_state,
            "current_action": self.current_action,
            "cognition": self.cognition,
            "active_thoughts": self.active_thoughts,
            "dominant_thought": self.dominant_thought,
        })
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        inv = [ItemInstance.from_dict(i) for i in data.get("inventory", [])]
        npc = cls(
            npc_id=data.get("id", data.get("npc_id", "npc")),
            name=data.get("name", "Citizen"),
            location_id=data.get("location_id"),
            occupation=data.get("occupation", "Commoner"),
            home_location_id=data.get("home_location_id"),
            work_location_id=data.get("work_location_id"),
            needs=data.get("needs"),
            decay_rates=data.get("decay_rates"),
            attributes=data.get("attributes"),
            personality=data.get("personality"),
            inventory=inv,
            wealth=float(data.get("wealth", 50.0)),
            faction_id=data.get("faction_id"),
            civic_role=data.get("civic_role"),
            social_profile=data.get("social_profile"),
            feelings=data.get("feelings"),
            moral_erosion=float(data.get("moral_erosion", 10.0)),
            skills=data.get("skills"),
            physical_attributes=data.get("physical_attributes"),
            mental_attributes=data.get("mental_attributes"),
            career_statistics=data.get("career_statistics"),
            vices=data.get("vices"),
            cognition=data.get("cognition"),
        )
        npc.current_state = data.get("current_state", "IDLE")
        npc.current_action = data.get("current_action", "IDLE")
        return npc
