"""
Elastic Maslow Hierarchy of Desires & Task Motivational Salience Index Engine.
Operates 100% on declarative configurations from data/settings/desire_hierarchy.json.
Models dynamic, elastic priority hierarchies shaped continuously by life stage, wealth,
fatigue, marital status, and environmental conditions without implicit state machines.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry


class NeedTier(str, Enum):
    PHYSIOLOGICAL = "PHYSIOLOGICAL"
    SAFETY_SECURITY = "SAFETY_SECURITY"
    LOVE_BELONGING = "LOVE_BELONGING"
    ESTEEM_MASTERY = "ESTEEM_MASTERY"
    SELF_ACTUALIZATION = "SELF_ACTUALIZATION"


@dataclass
class DesireProfile:
    npc_id: str
    tier_weights: Dict[str, float]
    financial_urgency_factor: float          # 0.03 (affluent) to 2.5 (destitute)
    somatic_rest_urgency: float              # 0.1 to 3.0 (continuous sleep pressure)
    somatic_hunger_urgency: float            # 0.1 to 3.5 (metabolic hunger urge)
    relationship_mode: str                   # "MARRIED_DEVOTION", "PARTNER_COHABITATION", "SINGLE_COURTSHIP"
    affiliation_drive: float                 # Social / belonging potential
    vocational_drive: float                  # Trade mastery / esteem potential
    overcrowding_drag: float                 # 0.0 (spacious) to 0.6 (crowded)
    comfort_modifier: float                  # 0.4 to 1.5 (quality of living space affordances)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "tier_weights": {k: round(v, 2) for k, v in self.tier_weights.items()},
            "financial_urgency_factor": round(self.financial_urgency_factor, 3),
            "somatic_rest_urgency": round(self.somatic_rest_urgency, 3),
            "somatic_hunger_urgency": round(self.somatic_hunger_urgency, 3),
            "relationship_mode": self.relationship_mode,
            "affiliation_drive": round(self.affiliation_drive, 2),
            "vocational_drive": round(self.vocational_drive, 2),
            "overcrowding_drag": round(self.overcrowding_drag, 2),
            "comfort_modifier": round(self.comfort_modifier, 2)
        }


class DesireHierarchyEngine:
    """
    Central Motivational Salience and Elastic Need Hierarchy Engine.
    Computes an agent's dynamic Maslow hierarchy and evaluates continuous Desire Indices
    for all candidate actions, preventing unneeded job hoarding and guiding natural rest,
    cohabitation, and domestic anchoring without rigid state machines.
    """
    _instance: Optional["DesireHierarchyEngine"] = None

    @classmethod
    def get_instance(cls) -> "DesireHierarchyEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent_profiles: Dict[str, DesireProfile] = {}
        self.total_evaluations_count: int = 0
        self._load_from_settings()

    def clear(self) -> None:
        self.agent_profiles.clear()
        self.total_evaluations_count = 0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        pass

    def get_hierarchy_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("desire_hierarchy").get("desire_hierarchy", {})

    def evaluate_agent_hierarchy(self, npc: Any, context: Any, current_tick: int) -> DesireProfile:
        """
        Dynamically computes an NPC's elastic Maslow need hierarchy based on:
        1. Physiological state: Hunger decay, Borbély sleep pressure S, temperature.
        2. Financial buffer & security: Wealth level relative to subsistence/affluence curves.
        3. Relational stage: Single courtship vs. married devotion and domestic harmony.
        4. Esteem & Craftsmanship: Vocational pride vs. menial casual work.
        5. Environmental shelter affordances and home overcrowding drag.
        """
        cfg = self.get_hierarchy_config()
        tiers_cfg = cfg.get("tiers", {})
        phys_cfg = tiers_cfg.get("PHYSIOLOGICAL", {})
        safe_cfg = tiers_cfg.get("SAFETY_SECURITY", {})
        love_cfg = tiers_cfg.get("LOVE_BELONGING", {})
        est_cfg = tiers_cfg.get("ESTEEM_MASTERY", {})
        act_cfg = tiers_cfg.get("SELF_ACTUALIZATION", {})
        cohab_cfg = cfg.get("cohabitation_dynamics", {})

        needs = getattr(npc, "needs", {}) or {}
        feelings = getattr(npc, "feelings", {}) or {}
        personality = getattr(npc, "personality", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}
        vices = getattr(npc, "vices", {}) or {}

        hunger = float(needs.get("hunger", 0.0))
        energy = float(needs.get("energy", 100.0))
        fatigue = max(0.0, 100.0 - energy)
        wealth = float(getattr(npc, "wealth", 0.0))
        stress = float(feelings.get("stress", 0.0))
        passion = float(feelings.get("passion", 0.0))
        tension = float(getattr(npc, "unmet_intimacy_tension", 0.0))
        cons = float(personality.get("conscientiousness", 0.5))
        ext = float(personality.get("extraversion", 0.5))
        amb = float(getattr(npc, "mental_attributes", {}).get("ambition", 50.0)) / 100.0

        # ---------------------------------------------------------------------
        # 1. PHYSIOLOGICAL TIER (Continuous Somatic Urgency)
        # ---------------------------------------------------------------------
        h_spec = phys_cfg.get("hunger", {})
        h_exp = float(h_spec.get("exponential_exponent", 1.6))
        h_urg_thresh = float(h_spec.get("urgency_threshold", 60.0))
        h_urgency = 0.20 + (hunger / 100.0)
        if hunger > h_urg_thresh:
            h_urgency += ((hunger - h_urg_thresh) / 20.0) ** h_exp

        r_spec = phys_cfg.get("rest", {})
        r_exp = float(r_spec.get("process_s_exponent", 2.2))
        r_thresh = float(r_spec.get("fatigue_threshold", 70.0))
        r_urgency = 0.20 + (fatigue / 100.0)
        if fatigue > r_thresh:
            r_urgency += ((fatigue - r_thresh) / 15.0) ** r_exp

        # Thermal comfort check
        t_spec = phys_cfg.get("thermal_comfort", {})
        room_temp = getattr(npc, "_current_room_temperature", 18.0)
        thermal_urgency = 0.0
        if room_temp < float(t_spec.get("comfort_band_low_celsius", 16.0)):
            thermal_urgency = max(0.0, (16.0 - room_temp) * 0.15)

        physio_weight = (h_urgency * 30.0) + (r_urgency * 35.0) + (thermal_urgency * 15.0)

        # ---------------------------------------------------------------------
        # 2. SAFETY & SECURITY TIER (Financial Buffer & Housing Stability)
        # ---------------------------------------------------------------------
        fin_spec = safe_cfg.get("financial_security", {})
        sub_gold = float(fin_spec.get("subsistence_reserve_gold", 15.0))
        comf_gold = float(fin_spec.get("comfortable_reserve_gold", 50.0))
        aff_gold = float(fin_spec.get("affluent_ceiling_gold", 120.0))
        p_exp = float(fin_spec.get("poverty_urgency_exponent", 1.5))
        damp_floor = float(fin_spec.get("wealthy_work_dampening_floor", 0.03))

        # Financial urgency factor (inversely proportional to wealth)
        if wealth < sub_gold:
            # High desperation: hunger/poverty urgency surges up to 2.5x
            fin_urgency = 1.0 + (((sub_gold - wealth) / max(1.0, sub_gold)) ** p_exp) * 1.5
        elif wealth < aff_gold:
            # Moderate comfort: work motivation naturally drops as wealth builds
            ratio = (wealth - sub_gold) / (aff_gold - sub_gold)
            fin_urgency = max(damp_floor, 1.0 - (ratio ** 1.2))
        else:
            # Affluent / Wealthy: casual work desire dampens to baseline floor (0.03)
            fin_urgency = damp_floor

        shelter_spec = safe_cfg.get("shelter_security", {})
        safety_weight = (fin_urgency * 35.0) + float(shelter_spec.get("home_hearth_warmth_weight", 20.0))

        # ---------------------------------------------------------------------
        # 3. LOVE & BELONGING TIER (Dynamic Courtship vs Marital Devotion)
        # ---------------------------------------------------------------------
        spouse_id = sp.get("spouse_id")
        partner_id = sp.get("partner_id")
        has_spouse = bool(spouse_id and hasattr(context, "npcs") and spouse_id in context.npcs)
        has_partner = bool(partner_id and hasattr(context, "npcs") and partner_id in context.npcs)

        belonging_weight = 20.0
        relationship_mode = "SINGLE_COURTSHIP"

        if has_spouse or has_partner:
            relationship_mode = "MARRIED_DEVOTION" if has_spouse else "PARTNER_COHABITATION"
            m_spec = love_cfg.get("marital_devotion", {})
            base_m = float(m_spec.get("base_drive_weight", 35.0))
            aff_scale = float(m_spec.get("spousal_affection_scaling", 0.45))

            # Retrieve spousal bond
            partner_npc_id = spouse_id or partner_id
            rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else None
            spousal_affection = 75.0
            spousal_resentment = 0.0

            if rom_eng and hasattr(rom_eng, "get_or_create_bond"):
                bond = rom_eng.get_or_create_bond(npc.id, partner_npc_id, context=context)
                spousal_affection = float(bond.romantic_affection)

            partner_npc = context.npcs.get(partner_npc_id)
            if partner_npc and hasattr(partner_npc, "get_feeling"):
                spousal_resentment = float(partner_npc.get_feeling("resentment"))

            # Domestic devotion: desire for spousal intimacy and household harmony
            belonging_weight = base_m + (spousal_affection * aff_scale) + float(m_spec.get("domestic_harmony_bonus", 15.0))
            if spousal_resentment > 15.0:
                belonging_weight = max(10.0, belonging_weight - float(m_spec.get("spousal_resentment_penalty", 25.0)))
        else:
            # Single / Unattached: Courtship, dating, and flirting motivation
            c_spec = love_cfg.get("courtship_unattached", {})
            base_c = float(c_spec.get("base_drive_weight", 25.0))
            belonging_weight = base_c + (passion * float(c_spec.get("passion_scaling", 0.35))) + (tension * float(c_spec.get("intimacy_tension_scaling", 0.35)))

        # Fraternal kinship & peer trust
        f_spec = love_cfg.get("fraternal_kinship", {})
        kinship_bonus = (ext * float(f_spec.get("extraversion_scaling", 22.0)))
        belonging_weight += kinship_bonus

        # ---------------------------------------------------------------------
        # 4. ESTEEM & VOCATIONAL MASTERY TIER
        # ---------------------------------------------------------------------
        v_spec = est_cfg.get("vocational_mastery", {})
        occ_l = (getattr(npc, "occupation", "") or "").lower()
        is_artisan = any(k in occ_l for k in ("baker", "smith", "blacksmith", "carpenter", "miller", "farmer", "weaver", "mason"))

        voc_stamina = max(0.15, energy / 100.0)
        esteem_weight = ((cons * float(v_spec.get("conscientiousness_scaling", 26.0))) +
                         (amb * float(v_spec.get("ambition_scaling", 18.0))) +
                         (float(v_spec.get("artisan_trade_bonus", 20.0)) if is_artisan else 10.0)) * voc_stamina

        # ---------------------------------------------------------------------
        # 5. SELF-ACTUALIZATION & ASPIRATIONAL TIER
        # ---------------------------------------------------------------------
        lg_eng = context.get_service("life_goal_engine") if hasattr(context, "get_service") else None
        goal_progress = lg_eng.calculate_progress(npc, context) if lg_eng else 0.50
        actualization_weight = (goal_progress * float(act_cfg.get("life_aspiration", {}).get("goal_progress_urgency", 25.0))) + float(act_cfg.get("recreation_and_contemplation", {}).get("leisure_base_potential", 14.0))

        # ---------------------------------------------------------------------
        # 6. HOUSING AFFORDANCES & OVERCROWDING EVALUATION
        # ---------------------------------------------------------------------
        home_loc = getattr(npc, "home_location_id", None)
        overcrowding_drag = 0.0
        comfort_modifier = 1.0

        if home_loc and hasattr(context, "npcs"):
            std_cap = int(cohab_cfg.get("standard_room_capacity", 2))
            pen_per_excess = float(cohab_cfg.get("overcrowding_penalty_per_excess_occupant", 0.25))
            max_drag = float(cohab_cfg.get("max_overcrowding_drag", 0.60))

            room_cohabitants = [
                n for n in context.npcs.values()
                if getattr(n, "home_location_id", None) == home_loc and getattr(n, "is_alive", True)
            ]
            excess = max(0, len(room_cohabitants) - std_cap)
            overcrowding_drag = min(max_drag, excess * pen_per_excess)

            # Check room interactive affordances
            comfort_modifier = max(0.40, (1.0 - overcrowding_drag) + (0.25 if "bedroom" in home_loc else 0.10))

        tier_weights = {
            NeedTier.PHYSIOLOGICAL.value: physio_weight,
            NeedTier.SAFETY_SECURITY.value: safety_weight,
            NeedTier.LOVE_BELONGING.value: belonging_weight,
            NeedTier.ESTEEM_MASTERY.value: esteem_weight,
            NeedTier.SELF_ACTUALIZATION.value: actualization_weight
        }

        profile = DesireProfile(
            npc_id=npc.id,
            tier_weights=tier_weights,
            financial_urgency_factor=fin_urgency,
            somatic_rest_urgency=r_urgency,
            somatic_hunger_urgency=h_urgency,
            relationship_mode=relationship_mode,
            affiliation_drive=belonging_weight,
            vocational_drive=esteem_weight,
            overcrowding_drag=overcrowding_drag,
            comfort_modifier=comfort_modifier
        )
        self.agent_profiles[npc.id] = profile
        self.total_evaluations_count += 1
        return profile

    def calculate_task_desire_index(
        self,
        npc: Any,
        task_category: str,
        base_reward: float = 0.0,
        context: Optional[Any] = None,
        current_tick: int = 0
    ) -> float:
        """
        Calculates a continuous Desire Index on any candidate task/action:
        - Casual menial labor scales strictly with financial urgency (wealthy artisans ignore menial jobs).
        - Sleep scales with Borbély Process S and home bed affordance comfort (reduced by overcrowding).
        - Domestic meals scale with hunger and home pantry stocks.
        - Courtship/intimacy scales with marital devotion or single courtship longing.
        """
        profile = self.agent_profiles.get(npc.id)
        if not profile and context:
            profile = self.evaluate_agent_hierarchy(npc, context, current_tick)
        if not profile:
            return 50.0

        cat_upper = task_category.upper()

        # 1. Casual / Menial Labor Postings (e.g. Tavern Dishwasher, Common Labor)
        if "CASUAL" in cat_upper or "COMMERCIAL_ASSISTANCE" in cat_upper or "DAY_LABOR" in cat_upper:
            # Clergy has zero desire for external menial odd jobs
            occ_l = (getattr(npc, "occupation", "") or "").lower()
            if any(k in occ_l for k in ("priest", "clergy", "monk", "curate")):
                return 0.01

            # Scaled strictly by financial urgency: a wealthy baker with 1,700g has factor 0.03!
            base_pull = (base_reward * 2.5) if base_reward > 0 else 15.0
            desire_index = base_pull * profile.financial_urgency_factor
            return round(max(0.10, desire_index), 2)

        # 2. Skilled Trade / Vocational Production (In-Shift Crafting)
        elif "VOCATIONAL" in cat_upper or "CRAFT" in cat_upper or "WORK" in cat_upper:
            base_pull = profile.vocational_drive
            # Financial need provides a boost, but trade mastery maintains baseline pride
            return round(base_pull * (0.60 + (profile.financial_urgency_factor * 0.40)), 2)

        # 3. Sleep & Rest
        elif "REST" in cat_upper or "SLEEP" in cat_upper:
            # Somatic sleep pressure modulated by living space comfort and overcrowding drag
            return round(profile.somatic_rest_urgency * 45.0 * profile.comfort_modifier, 2)

        # 4. Food & Sustenance
        elif "FOOD" in cat_upper or "EAT" in cat_upper or "HUNGER" in cat_upper:
            return round(profile.somatic_hunger_urgency * 40.0, 2)

        # 5. Courtship & Romance
        elif "ROMANCE" in cat_upper or "INTIMACY" in cat_upper or "COURTSHIP" in cat_upper:
            return round(profile.affiliation_drive * (1.20 if profile.relationship_mode == "MARRIED_DEVOTION" else 1.0), 2)

        # 6. Leisure & Tavern Games
        elif "GAME" in cat_upper or "LEISURE" in cat_upper or "RECREATION" in cat_upper:
            # Scaled by extraversion and leisure desire, dampened by extreme financial desperation or fatigue
            wealth = float(getattr(npc, "wealth", 0.0))
            affordability = min(1.0, wealth / 5.0)
            return round(profile.tier_weights.get(NeedTier.SELF_ACTUALIZATION.value, 15.0) * affordability * (1.0 - (profile.overcrowding_drag * 0.3)), 2)

        return 25.0

    def calculate_utility_modifiers(self, npc: Any, context: Any, current_tick: int) -> Dict[str, float]:
        """
        Injects continuous Desire Hierarchy modifiers directly into UtilityEvaluator:
        Couples physiological need urgency, wealth-scaled labor desire, and relational focus
        into candidate decision utilities smoothly without hardcoded state machine overrides.
        """
        profile = self.evaluate_agent_hierarchy(npc, context, current_tick)
        mods: Dict[str, float] = {}

        # 1. Food desire modulation
        if profile.somatic_hunger_urgency > 1.2:
            mods["satisfy_hunger"] = round((profile.somatic_hunger_urgency - 1.0) * 35.0, 2)
            mods["communal_dining"] = round((profile.somatic_hunger_urgency - 1.0) * 20.0, 2)

        # 2. Rest desire modulation (Borbély Process S continuous sleep pressure)
        if profile.somatic_rest_urgency > 1.2:
            # Fatigue builds up continuously from wakefulness; rest desire climbs smoothly
            mods["rest"] = round((profile.somatic_rest_urgency - 1.0) * 40.0 * profile.comfort_modifier, 2)
            # Sleep pressure naturally depresses voluntary labor and recreation
            mods["work_production"] = round(-min(30.0, (profile.somatic_rest_urgency - 1.0) * 25.0), 2)
            mods["socialize"] = round(-min(25.0, (profile.somatic_rest_urgency - 1.0) * 20.0), 2)

        # 3. Financial urgency modulation on work_production:
        # If affluent (wealth > 120g, factor 0.03), voluntary work drive is dampened;
        # if impoverished (wealth < 15g, factor > 1.0), work desire is heavily boosted.
        if profile.financial_urgency_factor < 0.20:
            # Affluent artisan: deprioritizes grinding labor, shifts energy to family, trade mastery, and leisure
            mods["work_production"] = mods.get("work_production", 0.0) - round((0.20 - profile.financial_urgency_factor) * 45.0, 2)
            if profile.relationship_mode == "MARRIED_DEVOTION":
                mods["socialize"] = mods.get("socialize", 0.0) + 15.0
                mods["communal_dining"] = mods.get("communal_dining", 0.0) + 12.0
        elif profile.financial_urgency_factor > 1.2:
            # Impoverished / destitute: financial survival surge
            mods["work_production"] = mods.get("work_production", 0.0) + round((profile.financial_urgency_factor - 1.0) * 35.0, 2)

        # 4. Relational stage modulation:
        if profile.relationship_mode == "MARRIED_DEVOTION":
            mods["socialize"] = mods.get("socialize", 0.0) + 12.0
            mods["communal_dining"] = mods.get("communal_dining", 0.0) + 8.0

        return mods
