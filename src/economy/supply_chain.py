"""
Commodity Supply Chains, Physical Crafting, and Dynamic Inventory Market Pricing.
Operates on declarative recipes, physical workstation capabilities,
weather-sensitive agricultural yields, and continuous supply-demand price elasticity.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from src.configuration.settings import SettingsRegistry
from src.entities.item import ItemInstance

@dataclass
class ProductionRecord:
    recipe_id: str
    artisan_id: str
    artisan_name: str
    location_id: str
    inputs_consumed: Dict[str, float]
    outputs_produced: Dict[str, float]
    quality_score: float
    tick: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "artisan_id": self.artisan_id,
            "artisan_name": self.artisan_name,
            "location_id": self.location_id,
            "inputs_consumed": self.inputs_consumed,
            "outputs_produced": self.outputs_produced,
            "quality_score": round(self.quality_score, 2),
            "tick": self.tick
        }

class CommoditySupplyChainEngine:
    """
    Central Physical Production & Supply Chain Engine.
    Manages physical commodity stocks, recipe execution at workstations,
    weather-modulated agricultural yields, and continuous price elasticity.
    """
    _instance: Optional["CommoditySupplyChainEngine"] = None

    @classmethod
    def get_instance(cls) -> "CommoditySupplyChainEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.commodity_stocks: Dict[str, float] = {}
        self.room_inventories: Dict[str, List[str]] = {}
        self.production_history: List[ProductionRecord] = []
        self.total_goods_produced_count: int = 0
        self.total_inputs_consumed_count: int = 0
        self.reseed_stocks()

    def reseed_stocks(self) -> None:
        """Reseeds commodity inventories to target baseline levels."""
        self.commodity_stocks = {
            "raw_wheat": 30.0,
            "flour": 20.0,
            "food_bread": 35.0,
            "raw_timber": 25.0,
            "firewood": 45.0,
            "furniture": 10.0,
            "raw_iron_ore": 25.0,
            "iron_ingot": 18.0,
            "iron_tools": 14.0,
            "oakwood_ale": 25.0
        }
        self.production_history.clear()

    def get_recipes_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("recipes").get("recipes", {})

    def get_chains_config(self) -> Dict[str, Any]:
        return SettingsRegistry.get_instance().get("supply_chains")

    def get_stock_level(self, item_def_id: str, settlement_id: Optional[str] = None) -> float:
        """Returns the current physical stock level of a commodity."""
        return float(self.commodity_stocks.get(item_def_id, 0.0))

    def add_stock(self, item_def_id: str, amount: float, room_id: Optional[str] = None) -> float:
        curr = self.commodity_stocks.get(item_def_id, 0.0)
        new_val = max(0.0, round(curr + amount, 2))
        self.commodity_stocks[item_def_id] = new_val
        if room_id:
            self.room_inventories.setdefault(room_id, []).append(item_def_id)
        return new_val

    def consume_stock(self, item_def_id: str, amount: float, room_id: Optional[str] = None) -> bool:
        curr = self.commodity_stocks.get(item_def_id, 0.0)
        if curr >= amount:
            self.commodity_stocks[item_def_id] = max(0.0, round(curr - amount, 2))
            return True
        return False

    def calculate_market_price(self, item_def_id: str, base_price: Optional[float] = None) -> float:
        """
        Continuous Price Elasticity Function:
        P_market = P_base * (TargetReserve / max(1.0, CurrentStock)) ^ Elasticity
        """
        sc_cfg = self.get_chains_config()
        market_cfg = sc_cfg.get("market_dynamics", {})
        baselines = market_cfg.get("target_reserve_baselines", {})

        spec = baselines.get(item_def_id, {})
        target_stock = float(spec.get("target_stock", 20.0))
        elasticity = float(spec.get("elasticity", 0.60))
        p_base = float(base_price or spec.get("base_price", 1.0))

        current_stock = max(1.0, self.get_stock_level(item_def_id))
        ratio = target_stock / current_stock
        multiplier = ratio ** elasticity

        min_mult = float(market_cfg.get("min_price_multiplier", 0.40))
        max_mult = float(market_cfg.get("max_price_multiplier", 3.50))
        clamped_mult = max(min_mult, min(max_mult, multiplier))

        return round(p_base * clamped_mult, 2)

    def execute_production_step(
        self,
        artisan: Any,
        recipe_id: str,
        context: Any,
        tick: int = 0
    ) -> Dict[str, Any]:
        """
        Executes a physical transformation step:
        1. Validates recipe declaration and inputs.
        2. Consumes physical inputs from storeroom/inventory.
        3. Scales quality and yield by artisan skill and ambient weather.
        4. Deposits outputs into physical stocks and awards career achievements.
        """
        recipes = self.get_recipes_config()
        if recipe_id not in recipes:
            return {"success": False, "reason": f"Recipe '{recipe_id}' not found in registry."}

        rec = recipes[recipe_id]
        inputs = rec.get("inputs", {})
        outputs = rec.get("outputs", {})
        worker_skill = rec.get("worker_skill", "crafting")
        weather_sensitive = rec.get("weather_sensitive", False)

        # 1. Input availability check
        for i_def, req_qty in inputs.items():
            if self.get_stock_level(i_def) < req_qty:
                return {
                    "success": False,
                    "reason": f"Insufficient input commodity '{i_def}' (needed {req_qty}, have {self.get_stock_level(i_def)})."
                }

        # 2. Consume inputs
        for i_def, req_qty in inputs.items():
            self.consume_stock(i_def, req_qty)
            self.total_inputs_consumed_count += int(req_qty)

        # 3. Quality & Yield Scaling based on continuous skill and weather
        skill_val = float(artisan.get_skill(worker_skill)) if hasattr(artisan, "get_skill") else 50.0
        quality = 0.50 + (skill_val / 100.0) * 0.80

        # Environmental & Meteorological Yield Scaling
        weather_mult = 1.0
        if weather_sensitive and context:
            clim_eng = context.get_service("micro_climate_engine")
            if clim_eng and hasattr(clim_eng, "current_weather") and clim_eng.current_weather:
                w = clim_eng.current_weather
                # Beneficial rainfall and spring/summer warmth
                if w.precipitation_intensity > 0.15 and w.ambient_temperature > 8.0:
                    weather_mult = 1.25  # Rain-irrigated harvest boom
                elif w.ambient_temperature < 0.0:
                    weather_mult = 0.65  # Freezing ground frost penalty

        # 4. Deposit physical outputs
        produced: Dict[str, float] = {}
        for out_def, base_qty in outputs.items():
            final_qty = round(base_qty * weather_mult, 2)
            self.add_stock(out_def, final_qty, room_id=artisan.location_id)
            produced[out_def] = final_qty
            self.total_goods_produced_count += int(final_qty)

        # 5. Career & Biographical Logging
        record = ProductionRecord(
            recipe_id=recipe_id,
            artisan_id=artisan.id,
            artisan_name=artisan.name,
            location_id=artisan.location_id or "room_workshop",
            inputs_consumed=inputs,
            outputs_produced=produced,
            quality_score=quality,
            tick=tick
        )
        self.production_history.append(record)

        if hasattr(artisan, "record_stat"):
            artisan.record_stat("goods_crafted_count", 1)

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        out_summary = ", ".join(f"{q:.1f}x {name}" for name, q in produced.items())
        artisan.record_biographical_entry(
            tick, time_iso, "COMMODITY_CRAFTING",
            f"Executed crafting recipe '{rec.get('name', recipe_id)}' producing {out_summary} (quality: {quality:.2f})."
        )

        return {
            "success": True,
            "recipe_id": recipe_id,
            "inputs_consumed": inputs,
            "outputs_produced": produced,
            "quality": quality,
            "weather_multiplier": weather_mult
        }

    def calculate_supply_urgency(self, item_def_id: str, threshold_stock: Optional[float] = None) -> float:
        """
        Continuous Supply Urgency Function (0.0 to 1.0):
        Upsilon = min(1.0, max(0.0, ((Target - Current) / Target) ^ gamma))
        """
        sc_cfg = self.get_chains_config()
        mech_cfg = sc_cfg.get("supply_chain_mechanics", {})
        urg_cfg = mech_cfg.get("urgency_scaling", {})
        gamma = float(urg_cfg.get("gamma", 1.2))

        target = float(threshold_stock) if threshold_stock is not None else 20.0
        curr = self.get_stock_level(item_def_id)
        if curr >= target:
            return 0.0

        deficit_ratio = max(0.0, (target - curr) / max(1.0, target))
        urgency = min(1.0, deficit_ratio ** gamma)
        return round(urgency, 3)

    def evaluate_artisan_supply_requirements(
        self,
        artisan: Any,
        context: Any,
        current_tick: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluates upstream supply chain dependencies for an artisan's industry.
        For each deficit, calculates continuous urgency, scaled reward/duration/priority,
        and competing utility potentials for Self-Completion vs. Subcontracting.
        """
        sc_cfg = self.get_chains_config()
        mech_cfg = sc_cfg.get("supply_chain_mechanics", {})
        urg_cfg = mech_cfg.get("urgency_scaling", {})
        dec_cfg = mech_cfg.get("decision_dynamics", {})
        industry_deps = mech_cfg.get("industry_upstream_dependencies", {})

        occ = (getattr(artisan, "occupation", "") or "").lower()
        matching_ind = None
        for ind_key, spec in industry_deps.items():
            if ind_key in occ:
                matching_ind = spec
                break

        if not matching_ind:
            return []

        dependencies = matching_ind.get("dependencies", [])
        requirements = []

        gamma = float(urg_cfg.get("gamma", 1.2))
        max_mult_boost = float(urg_cfg.get("max_wage_multiplier_boost", 0.75))
        pay_scale_factor = float(urg_cfg.get("pay_scaling_factor", 0.50))
        dur_red_ratio = float(urg_cfg.get("duration_reduction_ratio", 0.50))
        min_dur = int(urg_cfg.get("min_duration_ticks", 90))
        std_dur = int(urg_cfg.get("standard_duration_ticks", 240))
        std_validity = int(urg_cfg.get("standard_validity_ticks", 1440))
        urg_validity = int(urg_cfg.get("urgent_validity_ticks", 720))
        max_pri = float(urg_cfg.get("max_priority_score", 3.50))

        self_w = dec_cfg.get("self_completion_weights", {})
        sub_w = dec_cfg.get("subcontracting_weights", {})
        temp = float(dec_cfg.get("decision_temperature", 10.0))

        energy = float(getattr(artisan, "needs", {}).get("energy", 100.0))
        wealth = float(getattr(artisan, "wealth", 50.0))
        p = getattr(artisan, "personality", {}) or {}
        cons = float(p.get("conscientiousness", 0.5))
        amb = float(getattr(artisan, "mental_attributes", {}).get("ambition", 50.0)) / 100.0

        jp_eng = context.get_service("job_posting_engine") if hasattr(context, "get_service") else None

        for dep in dependencies:
            commodity = dep.get("required_commodity")
            threshold = float(dep.get("threshold_stock", 10.0))
            current_stock = self.get_stock_level(commodity)

            if current_stock < threshold:
                urgency = self.calculate_supply_urgency(commodity, threshold)

                # Scaled compensation and time parameters
                base_reward = float(dep.get("base_reward_gold", 5.0))
                base_multiplier = 1.0
                scaled_multiplier = round(base_multiplier + (urgency * max_mult_boost), 2)
                scaled_reward = round(base_reward * (1.0 + urgency * pay_scale_factor), 1)

                scaled_duration = max(min_dur, int(std_dur * (1.0 - dur_red_ratio * urgency)))
                scaled_validity = int(std_validity - (std_validity - urg_validity) * urgency)
                scaled_priority = round(1.0 + (urgency * (max_pri - 1.0)), 2)

                upstream_recipe_id = dep.get("upstream_recipe")
                upstream_skill = dep.get("upstream_skill", "crafting")
                worker_skill = float(artisan.get_skill(upstream_skill)) if hasattr(artisan, "get_skill") else 20.0

                # Utility A: Self-Completion
                u_skill = (worker_skill / 100.0) * float(self_w.get("skill_weight", 30.0))
                u_stamina = (energy / 100.0) * float(self_w.get("stamina_weight", 25.0))
                u_frugality = ((100.0 - min(100.0, wealth)) / 100.0) * float(self_w.get("frugality_weight", 20.0))
                u_cons = cons * float(self_w.get("conscientiousness_weight", 15.0))
                u_urg_self = urgency * float(self_w.get("urgency_bonus", 10.0))
                u_self_total = u_skill + u_stamina + u_frugality + u_cons + u_urg_self

                # Check if upstream recipe itself has available inputs
                recipes = self.get_recipes_config()
                up_rec = recipes.get(upstream_recipe_id, {})
                for in_k, in_q in up_rec.get("inputs", {}).items():
                    if self.get_stock_level(in_k) < in_q:
                        u_self_total *= 0.20

                # Utility B: Subcontracting via Job Posting
                cost_ratio = min(1.0, wealth / max(1.0, scaled_reward * 2.0))
                u_afford = cost_ratio * float(sub_w.get("affordability_weight", 35.0))
                u_fatigue = ((100.0 - energy) / 100.0) * float(sub_w.get("fatigue_weight", 25.0))
                u_spec = ((100.0 - worker_skill) / 100.0) * float(sub_w.get("specialization_weight", 20.0))
                u_amb = amb * float(sub_w.get("ambition_weight", 15.0))
                u_urg_sub = urgency * float(sub_w.get("urgency_bonus", 15.0))
                u_sub_total = u_afford + u_fatigue + u_spec + u_amb + u_urg_sub

                # Cannot hire if broke
                if wealth < scaled_reward:
                    u_sub_total = -999.0

                # Prevent duplicate postings by same employer
                has_existing = False
                if jp_eng and hasattr(jp_eng, "active_postings"):
                    has_existing = any(
                        p.category.value == "SUPPLY_CHAIN_REQUISITION"
                        and getattr(p, "required_commodity", "") == commodity
                        and getattr(p, "employer_id", "") == artisan.id
                        and p.status.value in ("OPEN", "CLAIMED")
                        for p in jp_eng.active_postings.values()
                    )
                if has_existing:
                    u_sub_total = -999.0

                # Softmax logit probabilities
                max_u = max(u_self_total, u_sub_total)
                exp_self = math.exp((u_self_total - max_u) / max(1.0, temp))
                exp_sub = math.exp((u_sub_total - max_u) / max(1.0, temp)) if u_sub_total > -500.0 else 0.0
                tot_exp = exp_self + exp_sub
                prob_self = exp_self / tot_exp if tot_exp > 0 else 1.0
                prob_sub = exp_sub / tot_exp if tot_exp > 0 else 0.0

                preferred = "SELF_COMPLETE" if prob_self >= prob_sub else "POST_JOB"

                requirements.append({
                    "commodity": commodity,
                    "threshold_stock": threshold,
                    "current_stock": current_stock,
                    "urgency": urgency,
                    "upstream_recipe": upstream_recipe_id,
                    "upstream_skill": upstream_skill,
                    "title": dep.get("title", f"Supply Requisition: {commodity}"),
                    "description": dep.get("description", ""),
                    "scaled_reward_gold": scaled_reward,
                    "scaled_wage_multiplier": scaled_multiplier,
                    "scaled_duration_ticks": scaled_duration,
                    "scaled_validity_ticks": scaled_validity,
                    "scaled_priority_score": scaled_priority,
                    "utility_self_complete": round(u_self_total, 2),
                    "utility_subcontract": round(u_sub_total, 2),
                    "prob_self_complete": round(prob_self, 3),
                    "prob_subcontract": round(prob_sub, 3),
                    "recommended_choice": preferred,
                })

        return requirements

    def resolve_artisan_supply_choice(
        self,
        artisan: Any,
        requirement_eval: Dict[str, Any],
        context: Any,
        current_tick: int,
        force_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the chosen resolution:
        1. SELF_COMPLETE: Artisan executes upstream recipe, benefits from value/earning and output.
        2. POST_JOB: Places dynamic supply chain job posting with urgency-scaled pay, duration, and priority.
        """
        choice = force_choice
        if not choice:
            roll = context.random.random() if hasattr(context, "random") and hasattr(context.random, "random") else 0.5
            choice = "SELF_COMPLETE" if roll < requirement_eval.get("prob_self_complete", 0.5) else "POST_JOB"

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        if choice == "SELF_COMPLETE":
            recipe_id = requirement_eval["upstream_recipe"]
            res = self.execute_production_step(artisan, recipe_id, context, tick=current_tick)
            if res.get("success"):
                # Direct labor earnings awarded to the artisan for their personal supply work
                from src.entities.occupations import OccupationRegistry
                occ_reg = OccupationRegistry.get_instance()
                occ_spec = occ_reg.get_occupation_spec(getattr(artisan, "occupation", ""))
                base_wage = float(occ_spec.get("base_hourly_wage", 1.20))
                work_rate = float(artisan.physical_attributes.get("work_rate", 55.0)) if hasattr(artisan, "physical_attributes") else 50.0
                earned = round(base_wage * (work_rate / 50.0), 2)
                artisan.wealth = round(artisan.wealth + earned, 2)
                if hasattr(artisan, "record_stat"):
                    artisan.record_stat("career_earnings_gold", earned)

                artisan.record_biographical_entry(
                    current_tick, time_iso, "SUPPLY_CHAIN_SELF_COMPLETION",
                    f"Personally completed upstream supply requirement '{recipe_id}' to produce {requirement_eval['commodity']}, benefiting directly from {earned:.1f}g labor value."
                )
                return {
                    "action": "SELF_COMPLETE",
                    "success": True,
                    "recipe_id": recipe_id,
                    "earned_gold": earned,
                    "produced": res.get("outputs_produced", {})
                }
            else:
                return {
                    "action": "SELF_COMPLETE",
                    "success": False,
                    "reason": res.get("reason", "Production step failed")
                }

        else:
            # POST_JOB (Subcontracting)
            jp_eng = context.get_service("job_posting_engine") if hasattr(context, "get_service") else None
            if not jp_eng:
                return {"action": "POST_JOB", "success": False, "reason": "Job posting engine not available"}

            from src.economy.job_postings import PostingChannel, JobPostingCategory
            public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
            target_work = artisan.work_location_id or artisan.location_id or public_plaza

            urgency = requirement_eval["urgency"]
            title_prefix = "Urgent Priority: " if urgency >= 0.6 else ""
            full_title = f"{title_prefix}{requirement_eval['title']}"

            post = jp_eng.create_posting(
                title=full_title,
                description=requirement_eval["description"],
                channel=PostingChannel.OFFICIAL,
                category=JobPostingCategory.SUPPLY_CHAIN_REQUISITION,
                location_id=public_plaza,
                target_work_location_id=target_work,
                reward_gold=requirement_eval["scaled_reward_gold"],
                employer_id=artisan.id,
                employer_name=artisan.name,
                wage_multiplier=requirement_eval["scaled_wage_multiplier"],
                required_skill=requirement_eval["upstream_skill"],
                min_skill_level=10.0,
                duration_ticks=requirement_eval["scaled_duration_ticks"],
                current_tick=current_tick,
                validity_duration_ticks=requirement_eval["scaled_validity_ticks"],
                priority_score=requirement_eval["scaled_priority_score"],
                urgency_level=urgency,
                recipe_id=requirement_eval["upstream_recipe"],
                required_commodity=requirement_eval["commodity"],
                context=context
            )

            artisan.record_biographical_entry(
                current_tick, time_iso, "SUPPLY_CHAIN_JOB_POSTED",
                f"Placed subcontracting requisition '{full_title}' for {requirement_eval['commodity']} on civic notice board (Reward: {post.reward_gold:.1f}g x{post.wage_multiplier:.2f}, Priority: {post.priority_score:.2f}x)."
            )

            # Broadcast to civic notices via UnifiedInformationSubsystem if available
            info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
            if info_eng and hasattr(info_eng, "publish_item"):
                from src.society.information_networks import InformationChannelType
                info_eng.publish_item(
                    channel=InformationChannelType.CIVIC_NOTICES,
                    topic=f"REQUISITION_{requirement_eval['commodity'].upper()}",
                    headline=f"Commercial Requisition: {full_title}",
                    content=f"{artisan.name} requisitions labor for {requirement_eval['commodity']}. Pay: {post.reward_gold:.1f}g. Priority: {post.priority_score:.1f}x.",
                    source_npc_id=artisan.id,
                    target_location_id=public_plaza,
                    current_tick=current_tick,
                    custom_duration=requirement_eval["scaled_validity_ticks"]
                )

            return {
                "action": "POST_JOB",
                "success": True,
                "posting_id": post.posting_id,
                "title": post.title,
                "reward_gold": post.reward_gold,
                "wage_multiplier": post.wage_multiplier,
                "duration_ticks": post.duration_ticks,
                "priority_score": post.priority_score,
                "urgency": urgency
            }

    def process_export_caravans(self, context: Any, current_tick: int) -> Optional[Dict[str, Any]]:
        """
        External Regional Trade Caravan (The ONLY legitimate source of new external wealth):
        Visits the settlement periodically (every 7 days) when exportable surpluses exist (> 150% target reserve).
        Purchases surplus commodities using external merchant gold, paying a 10% tariff to the Treasury
        and injects earned wealth to local producers.
        """
        if current_tick <= 0 or (current_tick % 10080 != 0 and current_tick % 14400 != 0):
            return None

        cfg = self.get_chains_config()
        market_cfg = cfg.get("market_dynamics", {})
        baselines = market_cfg.get("target_reserve_baselines", {})

        caravan_budget = 160.0
        purchases: Dict[str, float] = {}
        total_spent = 0.0
        treasury = getattr(context, "municipal_treasury", None)

        for item_def_id, base_spec in baselines.items():
            target = float(base_spec.get("target_stock", 20.0))
            current = self.get_stock_level(item_def_id)
            if current > (target * 1.5) and caravan_budget > 10.0:
                surplus = current - target
                export_qty = round(min(surplus * 0.35, 25.0), 1)
                unit_price = self.calculate_market_price(item_def_id)
                cost = round(export_qty * unit_price, 2)

                if cost <= caravan_budget and export_qty >= 0.5:
                    self.consume_stock(item_def_id, export_qty)
                    caravan_budget -= cost
                    total_spent += cost
                    purchases[item_def_id] = export_qty

                    tariff = round(cost * 0.10, 2)
                    producer_pay = round(cost - tariff, 2)
                    if treasury and hasattr(treasury, "balance") and tariff > 0:
                        treasury.balance = round(treasury.balance + tariff, 2)

                    producer = None
                    if "bread" in item_def_id or "flour" in item_def_id:
                        producer = context.find_npc_by_role(["baker", "miller", "farmer"]) if hasattr(context, "find_npc_by_role") else None
                    elif "timber" in item_def_id or "furniture" in item_def_id or "firewood" in item_def_id:
                        producer = context.find_npc_by_role(["carpenter", "woodcutter", "laborer"]) if hasattr(context, "find_npc_by_role") else None
                    elif "iron" in item_def_id or "tools" in item_def_id:
                        producer = context.find_npc_by_role(["smith", "blacksmith"]) if hasattr(context, "find_npc_by_role") else None
                    elif "ale" in item_def_id:
                        producer = context.find_npc_by_role(["innkeeper", "brewer"]) if hasattr(context, "find_npc_by_role") else None

                    if producer and getattr(producer, "is_alive", True):
                        producer.wealth = round(producer.wealth + producer_pay, 2)
                        producer.record_stat("career_earnings_gold", producer_pay)

        if purchases:
            time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
            summary_str = ", ".join(f"{q:.1f}x {k}" for k, q in purchases.items())
            info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
            if info_eng and hasattr(info_eng, "publish_item"):
                public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
                from src.society.information_networks import InformationChannelType
                info_eng.publish_item(
                    channel=InformationChannelType.CIVIC_NOTICES,
                    topic="EXPORT_TRADE_CARAVAN",
                    headline="Regional Export Caravan Purchases Settlement Surplus",
                    content=f"Regional merchant caravan purchased {summary_str} for {total_spent:.1f}g (tariff: {total_spent*0.1:.1f}g).",
                    target_location_id=public_plaza,
                    current_tick=current_tick,
                    custom_duration=10080
                )
            return {"success": True, "total_spent": total_spent, "purchases": purchases}
        return None

    def process_production_cycle(self, context: Any, tick: int, delta_ticks: int = 1) -> int:
        """
        Dispatched at TickStage.ECONOMIC_PRODUCTION:
        Coordinates working artisans with matching trade recipes in their active workshops.
        """
        if not hasattr(context, "npcs") or not context.npcs:
            return 0

        # Map occupations to primary production recipes
        occ_recipe_map = {
            "farmer": "harvest_wheat",
            "miller": "mill_flour",
            "baker": "bake_bread",
            "carpenter": "craft_furniture",
            "smith": "forge_tools",
            "blacksmith": "forge_tools",
            "innkeeper": "brew_ale",
            "woodcutter": "fell_timber",
            "laborer": "split_firewood"
        }

        production_events = 0
        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            curr_act = (getattr(npc, "current_action", "") or "").upper()
            if not ("LABOR" in curr_act or "JOB_" in curr_act or "CRAFT" in curr_act):
                continue

            occ = (getattr(npc, "occupation", "") or "").lower()
            matching_recipe = None

            if "baker" in occ:
                if self.get_stock_level("flour") < 1.0 and self.get_stock_level("raw_wheat") >= 1.0:
                    matching_recipe = "mill_flour"
                else:
                    matching_recipe = "bake_bread"
            elif "miller" in occ:
                matching_recipe = "mill_flour"
            elif "farmer" in occ:
                if self.get_stock_level("flour") < 8.0 and self.get_stock_level("raw_wheat") >= 2.0:
                    matching_recipe = "mill_flour"
                else:
                    matching_recipe = "harvest_wheat"
            elif any(k in occ for k in ("laborer", "woodcutter")):
                firewood_stock = self.get_stock_level("firewood")
                timber_stock = self.get_stock_level("raw_timber")
                if firewood_stock >= 40.0 and timber_stock < 25.0:
                    matching_recipe = "fell_timber"
                elif firewood_stock < 40.0 and timber_stock >= 1.0:
                    matching_recipe = "split_firewood"
                elif timber_stock < 15.0:
                    matching_recipe = "fell_timber"
                else:
                    matching_recipe = "fell_timber"
            elif any(k in occ for k in ("smith", "blacksmith")):
                if self.get_stock_level("iron_ingot") < 8.0 and self.get_stock_level("raw_iron_ore") >= 1.0:
                    matching_recipe = "smelt_iron"
                else:
                    matching_recipe = "forge_tools"
            elif "carpenter" in occ:
                matching_recipe = "craft_furniture"
            elif "innkeeper" in occ:
                matching_recipe = "brew_ale"
            else:
                for occ_k, r_id in occ_recipe_map.items():
                    if occ_k in occ:
                        matching_recipe = r_id
                        break

            if matching_recipe:
                rec_def = self.get_recipes_config().get(matching_recipe, {})
                has_all_inputs = True
                for in_def, in_qty in rec_def.get("inputs", {}).items():
                    if self.get_stock_level(in_def) < in_qty:
                        has_all_inputs = False
                        break

                if has_all_inputs:
                    res = self.execute_production_step(npc, matching_recipe, context, tick)
                    if res.get("success"):
                        production_events += 1
                else:
                    # Input deficit in supply chain! Evaluate self-completion vs subcontracting posting
                    reqs = self.evaluate_artisan_supply_requirements(npc, context, tick)
                    if reqs:
                        res = self.resolve_artisan_supply_choice(npc, reqs[0], context, tick)
                        if res.get("success"):
                            production_events += 1

        return production_events
