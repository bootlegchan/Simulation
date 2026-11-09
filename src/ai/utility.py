"""Utility Evaluator with Declarative Drives, Continuous S-Curves and Softmax Logit Sampling."""
import math
from typing import Any, Dict, List, Optional, Tuple
from src.configuration.settings import SettingsRegistry

class UtilityEvaluator:
    @staticmethod
    def get_config() -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("drives")

    @staticmethod
    def evaluate_drives(
        needs: Dict[str, float],
        personality: Dict[str, float],
        env_modifiers: Optional[Dict[str, float]] = None,
        **kwargs: Any
    ) -> Dict[str, float]:
        """
        Continuous Multi-Attribute Drive Potential Evaluation.
        Loaded dynamically from data/settings/drives.json.
        """
        env_mods = env_modifiers or {}
        utilities: Dict[str, float] = {}

        drives_cfg = SettingsRegistry.get_instance().get("drives")
        d_specs = drives_cfg.get("drives", {})

        hunger = float(needs.get("hunger", 0.0))
        energy = float(needs.get("energy", 100.0))
        fatigue = max(0.0, 100.0 - energy)

        # 1. Continuous Somatic Hunger Gradient
        h_spec = d_specs.get("satisfy_hunger", {})
        h_lin = float(h_spec.get("linear_weight", 0.40))
        h_div = float(h_spec.get("scale_divisor", 28.0))
        h_pow = float(h_spec.get("power_exponent", 2.2))
        h_mult = float(h_spec.get("power_multiplier", 9.0))
        utilities["satisfy_hunger"] = (
            (hunger * h_lin) +
            ((hunger / h_div) ** h_pow) * h_mult +
            env_mods.get("satisfy_hunger", 0.0)
        )

        # 2. Continuous Somatic Sleep Pressure (Borbély Process S)
        r_spec = d_specs.get("rest", {})
        r_lin = float(r_spec.get("linear_weight", 0.25))
        r_div = float(r_spec.get("scale_divisor", 22.0))
        r_pow = float(r_spec.get("power_exponent", 2.3))
        r_mult = float(r_spec.get("power_multiplier", 6.0))
        utilities["rest"] = (
            (fatigue * r_lin) +
            ((fatigue / r_div) ** r_pow) * r_mult +
            env_mods.get("rest", 0.0)
        )

        # 3. Vocational Labor Potential
        w_spec = d_specs.get("work_production", {})
        cons_w = float(w_spec.get("conscientiousness_weight", 26.0))
        amb_w = float(w_spec.get("ambition_weight", 16.0))
        base_pot = float(w_spec.get("base_potential", 12.0))
        min_stamina = float(w_spec.get("min_stamina_factor", 0.15))

        cons = float(personality.get("conscientiousness", 0.5))
        amb = float(kwargs.get("ambition", 0.5))
        stamina_factor = max(min_stamina, energy / 100.0)
        utilities["work_production"] = (
            ((cons * cons_w) + (amb * amb_w) + base_pot) * stamina_factor +
            env_mods.get("work_production", 0.0)
        )

        # 4. Socialization & Community Dining
        s_spec = d_specs.get("socialize", {})
        ext_w = float(s_spec.get("extraversion_weight", 22.0))
        soc_def_w = float(s_spec.get("social_deficit_weight", 0.35))
        min_soc_stamina = float(s_spec.get("min_social_stamina", 0.15))

        ext = float(personality.get("extraversion", 0.5))
        social_deficit = max(0.0, 100.0 - float(needs.get("social", 50.0)))
        social_stamina = max(min_soc_stamina, (energy - 15.0) / 85.0)
        utilities["socialize"] = (
            ((ext * ext_w) + (social_deficit * soc_def_w)) * social_stamina +
            env_mods.get("socialize", 0.0)
        )

        cd_spec = d_specs.get("communal_dining", {})
        cd_base = float(cd_spec.get("base_potential", 14.0))
        cd_soc_w = float(cd_spec.get("social_deficit_weight", 0.20))
        cd_h_w = float(cd_spec.get("hunger_weight", 0.20))
        utilities["communal_dining"] = (
            ((cd_base + social_deficit * cd_soc_w) + (hunger * cd_h_w)) * social_stamina +
            env_mods.get("communal_dining", 0.0)
        )

        # 5. Continuous Thermal Comfort Gradient (Warmth Seeking in Cold Environments)
        r_temp = kwargs.get("room_temperature")
        if r_temp is not None and r_temp < 16.0:
            cold_pull = max(0.0, (18.0 - float(r_temp)) * 1.5)
            utilities["communal_dining"] = utilities.get("communal_dining", 0.0) + cold_pull
            utilities["rest"] = utilities.get("rest", 0.0) + (cold_pull * 0.5)

        # 6. Aspirational Life Goal Continuous Utility Steering Modifiers
        lg_mods = kwargs.get("life_goal_modifiers", {})
        if lg_mods:
            for d_name, mult in lg_mods.items():
                if d_name in utilities:
                    utilities[d_name] *= float(mult)

        # 7. Attentional Mindspace Dynamic Thought Biases
        att_biases = kwargs.get("attentional_biases", {})
        if att_biases:
            for d_name, bias_val in att_biases.items():
                if d_name in utilities:
                    utilities[d_name] += float(bias_val)

        return utilities

    @staticmethod
    def calculate_softmax_probabilities(utilities: Dict[str, float], temperature: Optional[float] = None) -> Dict[str, float]:
        if temperature is None:
            drives_cfg = SettingsRegistry.get_instance().get("drives")
            temperature = float(drives_cfg.get("decision_temperature", 12.0))
        temp = max(0.5, temperature)
        max_u = max(utilities.values()) if utilities else 0.0
        exp_vals = {k: math.exp((u - max_u) / temp) for k, u in utilities.items()}
        total_exp = sum(exp_vals.values())
        return {k: v / total_exp for k, v in exp_vals.items()} if total_exp > 0 else {}

    @staticmethod
    def sample_choice_multinomial_logit(utilities: Dict[str, float], rng: Any, temperature: Optional[float] = None) -> Tuple[str, float, Dict[str, float]]:
        probs = UtilityEvaluator.calculate_softmax_probabilities(utilities, temperature)
        if not probs:
            return ("rest", 1.0, {})

        roll = rng.random()
        cumulative = 0.0
        chosen = list(probs.keys())[0]
        for k, p in probs.items():
            cumulative += p
            if roll <= cumulative:
                chosen = k
                break
        return (chosen, probs.get(chosen, 0.0), probs)
